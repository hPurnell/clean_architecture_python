import logging

from dishka.integrations.faststream import FromDishka

from app import FastStreamRouter
from app.items.domain import Item, AbstractUnitOfWork

logger = logging.getLogger(__name__)
router = FastStreamRouter(prefix="item_service_")


@router.subscriber("create_command")
async def create_item(item: Item, unit_of_work: FromDishka[AbstractUnitOfWork]) -> None:
    item: Item | None = unit_of_work.items.create(item)
    if not item:
        logger.error(f"Unable to create item: {item}")
        raise Exception(detail="Unable to create item")
    unit_of_work.commit()
    logger.info(f"Item created: {item}")


@router.subscriber("update_command")
async def update_item(item: Item, unit_of_work: FromDishka[AbstractUnitOfWork]) -> None:
    item: Item | None = unit_of_work.items.update(item)
    if not item:
        logger.error(f"Unable to update item: {item}")
        raise Exception(detail=f"Unable to update item: {item}")
    unit_of_work.commit()
    logger.info(f"Item updated: {item}")


@router.subscriber("delete_command")
async def delete_item(
    item_id: int, unit_of_work: FromDishka[AbstractUnitOfWork]
) -> None:
    success: bool = unit_of_work.items.delete(item_id)
    if not success:
        logger.error(f"Unable to delete item: {item_id}")
        raise Exception(detail=f"Unable to delete item: {item_id}")
    unit_of_work.commit()
    logger.info(f"Item updated: {item_id}")
