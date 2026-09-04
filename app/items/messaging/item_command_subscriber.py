import logging
from typing import Any

from dishka.integrations.faststream import FromDishka

from app.broker import create_router
from app.items.messaging.item_commands import (
    CreateItemCommand,
    DeleteItemCommand,
    UpdateItemCommand,
    from_create_command,
    from_update_command,
)
from app.items.service.item_service import ItemService
from app.jobs.service.job_service import JobService

logger = logging.getLogger(__name__)

# A transport adapter only: the same ItemService the HTTP controller uses.


def create_item_command_router() -> Any:
    """Build a router carrying the item command subscribers.

    A factory, not a module-level router: a shared one would leave stale
    consumers on the queues of every app built in the process.
    """
    router = create_router("item_service_")

    @router.subscriber("create_command")  # type: ignore[misc]
    async def create_item(
        command: CreateItemCommand,
        item_service: FromDishka[ItemService],
        job_service: FromDishka[JobService],
    ) -> None:
        with job_service.track(command.job_id) as job:
            created_item = item_service.create_item(from_create_command(command))
            job.result = str(created_item.id)
            logger.info(f"Item created: {created_item}")

    @router.subscriber("update_command")  # type: ignore[misc]
    async def update_item(
        command: UpdateItemCommand,
        item_service: FromDishka[ItemService],
        job_service: FromDishka[JobService],
    ) -> None:
        with job_service.track(command.job_id) as job:
            updated_item = item_service.update_item(from_update_command(command))
            job.result = str(updated_item.id)
            logger.info(f"Item updated: {updated_item}")

    @router.subscriber("delete_command")  # type: ignore[misc]
    async def delete_item(
        command: DeleteItemCommand,
        item_service: FromDishka[ItemService],
        job_service: FromDishka[JobService],
    ) -> None:
        with job_service.track(command.job_id) as job:
            item_service.delete_item(command.id)
            job.result = str(command.id)
            logger.info(f"Item deleted: {command.id}")

    return router
