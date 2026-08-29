"""Message broker selection.

The concrete FastStream broker is chosen here, from configuration, rather than
being hard-coded in ``app/__init__.py``. Two things follow from that:

* importing anything under ``app.`` no longer drags in a broker driver, and
* switching broker is a configuration change (``MESSAGE_BROKER_TYPE``) rather
  than an edit to the root package.

Drivers are imported lazily so that only the selected backend needs to be
installed.
"""

from importlib import import_module
from typing import Any

from app.config import config

# backend name -> (module, broker class, router class)
BROKER_BACKENDS: dict[str, tuple[str, str, str]] = {
    "rabbit": ("faststream.rabbit", "RabbitBroker", "RabbitRouter"),
    "kafka": ("faststream.kafka", "KafkaBroker", "KafkaRouter"),
    "redis": ("faststream.redis", "RedisBroker", "RedisRouter"),
}


def _load_backend(name: str) -> tuple[type[Any], type[Any]]:
    try:
        module_path, broker_name, router_name = BROKER_BACKENDS[name]
    except KeyError:
        supported = ", ".join(sorted(BROKER_BACKENDS))
        raise ValueError(
            f"Unsupported MESSAGE_BROKER_TYPE {name!r}. Supported: {supported}."
        ) from None
    module = import_module(module_path)
    return getattr(module, broker_name), getattr(module, router_name)


Broker, BrokerRouter = _load_backend(config.MESSAGE_BROKER_TYPE)


def create_broker() -> Any:
    """Build the broker for the configured backend and URL."""
    return Broker(config.MESSAGE_BROKER_URL)


def create_router(prefix: str) -> Any:
    """Build a router for the configured backend."""
    return BrokerRouter(prefix=prefix)
