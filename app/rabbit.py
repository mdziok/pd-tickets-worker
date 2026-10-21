import logging
import pika

from config import RabbitSettings

logger = logging.getLogger(__name__)


def connect(settings: RabbitSettings) -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(settings.username, settings.password)
    parameters = pika.ConnectionParameters(
        host=settings.host,
        port=settings.port,
        virtual_host=settings.vhost,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
        connection_attempts=5,
        retry_delay=3,
        socket_timeout=10,
    )
    return pika.BlockingConnection(parameters)


def declare_queue(channel: pika.adapters.blocking_connection.BlockingChannel,
                  queue: str) -> None:
    # Musi odpowiadać istniejącej konfiguracji kolejki, jeśli już istnieje.
    channel.queue_declare(queue=queue, durable=True)



def publish_confirmed(channel, queue: str, body: bytes,
                      message_id: str | None = None) -> None:
    properties = pika.BasicProperties(
        content_type="application/json",
        content_encoding="utf-8",
        delivery_mode=2,
        message_id=message_id,
    )
    # Włączone confirm_delivery sprawia, że niepotwierdzona publikacja
    # zgłosi wyjątek (lub zwróci False, zależnie od sytuacji).
    confirmed = channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=body,
        properties=properties,
        mandatory=True,
    )
    if confirmed is False:
        raise RuntimeError("Broker docelowy nie potwierdził publikacji")
