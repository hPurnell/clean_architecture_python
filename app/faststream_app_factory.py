from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from faststream import FastStream
from litestar import Litestar

from app.broker import create_broker
from app.items.messaging import item_command_subscriber


def create_faststream_app() -> FastStream:
    broker = create_broker()
    broker.include_router(item_command_subscriber.router)
    return FastStream(broker)


@asynccontextmanager
async def lifespan_broker(app: Litestar) -> AsyncIterator[None]:
    broker: Any = app.state.broker
    await broker.start()
    try:
        yield
    finally:
        await broker.close()
