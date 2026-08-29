from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from faststream import FastStream
from litestar import Litestar

from app.broker import create_broker
from app.items.messaging.item_command_subscriber import create_item_command_router


def create_faststream_app() -> FastStream:
    broker = create_broker()
    # A router of its own, so this app's subscribers are not shared with any
    # other app built in the same process. See create_item_command_router.
    broker.include_router(create_item_command_router())
    return FastStream(broker)


@asynccontextmanager
async def lifespan_broker(app: Litestar) -> AsyncIterator[None]:
    broker: Any = app.state.broker
    await broker.start()
    try:
        yield
    finally:
        await broker.close()
