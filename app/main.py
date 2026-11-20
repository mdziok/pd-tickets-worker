import logging
import signal
import time

import pika

from config import LOG_LEVEL, PREFETCH_COUNT, SOURCE, TARGET
from processor import process_message
from rabbit import connect, declare_queue, publish_confirmed

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
    target_connection = None
    try:
        logger.info("Łączenie ze źródłowym RabbitMQ: %s:%s", SOURCE.host, SOURCE.port)
        source_connection = connect(SOURCE)
        source_channel = source_connection.channel()
        declare_queue(source_channel, SOURCE.queue)
        source_channel.basic_qos(prefetch_count=PREFETCH_COUNT)

        # logger.info("Łączenie z docelowym RabbitMQ: %s:%s", TARGET.host, TARGET.port)
        # target_connection = connect(TARGET)
        # target_channel = target_connection.channel()
        declare_queue(source_channel, TARGET.queue)
        source_channel.confirm_delivery()

        def callback(ch, method, properties, body: bytes):
            try:
                result = process_message(body)
                publish_confirmed(
                    source_channel,
                    TARGET.queue,
                    result,
                    message_id=getattr(properties, "message_id", None),
                )
            except ValueError:
                # TODO - co z błednymi wiadomościami?
                # Błędne dane nie będą zapętlane w kolejce źródłowej.
                # W wersji podstawowej odrzucamy je bez requeue; dodaj DLQ,
                # jeśli potrzebujesz zachować błędne wiadomości.
                logger.exception("Niepoprawna wiadomość — odrzucam bez ponowienia")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception:
                # Błąd publikacji/połączenia: wiadomość źródłowa pozostaje
                # do ponownego dostarczenia. Możliwe są duplikaty w celu
                # osiągnięcia at-least-once.
                logger.exception("Nie udało się przetworzyć/opublikować wiadomości")
                try:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                except pika.exceptions.AMQPError:
                    logger.exception("Nie udało się wysłać NACK")
            else:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info("Wiadomość przetworzona i opublikowana")

        source_channel.basic_consume(
            queue=SOURCE.queue,
            on_message_callback=callback,
            auto_ack=False,
        )
        logger.info("Nasłuchiwanie kolejki '%s'; cel: '%s'",
                    SOURCE.queue, TARGET.queue)

        while not _stopping and source_connection.is_open:
            source_connection.process_data_events(time_limit=1)

    finally:
        for connection in (source_connection, target_connection):
            if connection is not None and connection.is_open:
                try:
                    connection.close()
                except pika.exceptions.AMQPError:
                    logger.exception("Błąd podczas zamykania połączenia")


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
