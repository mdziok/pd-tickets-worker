import os
from dataclasses import dataclass


def _required(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise ValueError(f"Brak wymaganej zmiennej środowiskowej: {name}")
    return value


@dataclass(frozen=True)
class RabbitSettings:
    host: str
    port: int
    username: str
    password: str
    vhost: str
    queue: str


def _rabbit_settings(prefix: str, default_queue: str) -> RabbitSettings:
    return RabbitSettings(
        host=_required(f"{prefix}_HOST"),
        port=int(os.getenv(f"{prefix}_PORT", "5672")),
        username=_required(f"{prefix}_USER"),
        password=_required(f"{prefix}_PASSWORD"),
        vhost=os.getenv(f"{prefix}_VHOST", "/"),
        queue=os.getenv(f"{prefix}_QUEUE", default_queue),
    )


SOURCE = _rabbit_settings("SOURCE_RABBITMQ", "incoming")
TARGET = _rabbit_settings("TARGET_RABBITMQ", "processed")
# TARGET = _rabbit_settings("TARGET_RABBITMQ", "processed")
PREFETCH_COUNT = max(1, int(os.getenv("PREFETCH_COUNT", "10")))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
