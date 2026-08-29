from typing import Any

from app.items.domain.abstract_command_publisher import AbstractItemCommandPublisher
from app.items.domain.item import Item
from app.items.messaging.item_commands import (
    to_create_command,
    to_delete_command,
    to_update_command,
)

CREATE_COMMAND_SUBJECT = "item_service_create_command"
UPDATE_COMMAND_SUBJECT = "item_service_update_command"
DELETE_COMMAND_SUBJECT = "item_service_delete_command"


class ItemCommandPublisher(AbstractItemCommandPublisher):
    """Adapter that maps domain objects onto the message contract."""

    def __init__(self, broker: Any) -> None:
        self.broker = broker

    async def create_item(self, item: Item, job_id: str) -> None:
        await self.broker.publisher(CREATE_COMMAND_SUBJECT).publish(
            to_create_command(item, job_id)
        )

    async def update_item(self, item: Item, job_id: str) -> None:
        await self.broker.publisher(UPDATE_COMMAND_SUBJECT).publish(
            to_update_command(item, job_id)
        )

    async def delete_item(self, item_id: int, job_id: str) -> None:
        await self.broker.publisher(DELETE_COMMAND_SUBJECT).publish(
            to_delete_command(item_id, job_id)
        )
