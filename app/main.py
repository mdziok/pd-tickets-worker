import logging
import signal
import time

import pika

from config import LOG_LEVEL, PREFETCH_COUNT, SOURCE, TARGET
from processor import process_message
from rabbit import connect, declare_queue, declare_dead_letter_queue, publish_confirmed
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("rabbitmq_worker")

_stopping = False


def _stop(_signum, _frame):
    global _stopping
    _stopping = True
    logger.info("Otrzymano sygnał zatrzymania")


def run_once() -> None:
    source_connection = None
    executor = ThreadPoolExecutor(max_workers=1)

    try:
        logger.info(
            "Łączenie ze źródłowym RabbitMQ: %s:%s",
            SOURCE.host,
            SOURCE.port,
        )

        source_connection = connect(SOURCE)
        source_channel = source_connection.channel()

        declare_queue(source_channel, SOURCE.queue)
        declare_queue(source_channel, TARGET.queue)
        declare_dead_letter_queue(source_channel, SOURCE.queue)

        source_channel.basic_qos(prefetch_count=1)
        source_channel.confirm_delivery()

        def callback(ch, method, properties, body: bytes):
            delivery_tag = method.delivery_tag
            message_id = getattr(properties, "message_id", None)

            logger.info(
                "Odebrano zgłoszenie, message_id=%s",
                message_id,
            )

            future = executor.submit(process_message, body)

            def on_finished(future):
                def finish_on_rabbit_thread():
                    if not ch.is_open:
                        logger.warning(
                            "Kanał RabbitMQ został zamknięty przed zakończeniem analizy"
                        )
                        return

                    try:
                        result = future.result()

                        publish_confirmed(
                            ch,
                            TARGET.queue,
                            result,
                            message_id=message_id,
                        )

                    except ValueError:
                        logger.exception(
                            "Niepoprawna wiadomość — odrzucam bez ponowienia"
                        )
                        ch.basic_nack(
                            delivery_tag=delivery_tag,
                            requeue=False,
                        )

                    except Exception:
                        logger.exception(
                            "Błąd przetwarzania lub publikacji — przekazuję do DLQ"
                        )

                        if ch.is_open:
                            ch.basic_nack(
                                delivery_tag=delivery_tag,
                                requeue=False,
                            )

                    else:
                        ch.basic_ack(delivery_tag=delivery_tag)
                        logger.info(
                            "Wiadomość przetworzona i opublikowana"
                        )

                if source_connection.is_open:
                    try:
                        source_connection.add_callback_threadsafe(
                            finish_on_rabbit_thread
                        )
                    except pika.exceptions.AMQPError:
                        logger.exception(
                            "Nie udało się przekazać wyniku do RabbitMQ"
                        )

            future.add_done_callback(on_finished)

        source_channel.basic_consume(
            queue=SOURCE.queue,
            on_message_callback=callback,
            auto_ack=False,
        )

        logger.info(
            "Nasłuchiwanie kolejki '%s'; cel: '%s'",
            SOURCE.queue,
            TARGET.queue,
        )

        while not _stopping and source_connection.is_open:
            source_connection.process_data_events(time_limit=1)

    finally:
        if source_connection is not None and source_connection.is_open:
            try:
                source_connection.close()
            except pika.exceptions.AMQPError:
                logger.exception(
                    "Błąd podczas zamykania połączenia"
                )

        executor.shutdown(wait=True)


def main() -> None:
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    while not _stopping:
        try:
            run_once()
        except Exception:
            if _stopping:
                break
            logger.exception("Błąd pętli głównej; ponawiam za 5 sekund")
            time.sleep(5)

    logger.info("Aplikacja zatrzymana")


if __name__ == "__main__":
    main()
