import logging

from litestar.controller import Controller
from litestar.handlers.http_handlers.decorators import delete, patch, post, get
from litestar.exceptions import HTTPException
from dishka.integrations.litestar import inject, FromDishka

from app.items.domain import Item, AbstractUnitOfWork
from app.items.controllers import ItemDTO, NewItemDTO, UpdateItemDTO

logger = logging.getLogger(__name__)


class ItemController(Controller):
    path = "/items"
    tags = ["Items"]

    @get(path="", return_dto=ItemDTO)
    @inject
    async def get_items(
        self, unit_of_work: FromDishka[AbstractUnitOfWork]
    ) -> list[Item]:
        items: list[Item] = unit_of_work.items.get_all()
        return items

    @get(path="/{item_id:int}", return_dto=ItemDTO)
    @inject
    async def get_item(
        self, item_id: int, unit_of_work: FromDishka[AbstractUnitOfWork]
    ) -> Item | None:
        item: Item | None = unit_of_work.items.get(item_id)
        if not item:
            logger.error(f"Item not found: {item_id}")
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    @post(path="", dto=NewItemDTO, return_dto=ItemDTO)
    @inject
    async def post_item(
        self, data: Item, unit_of_work: FromDishka[AbstractUnitOfWork]
    ) -> Item:
        item: Item | None = unit_of_work.items.create(data)
        if not item:
            logger.error(f"Unable to create item: {data}")
            raise HTTPException(status_code=400, detail="Unable to create item")
        unit_of_work.commit()
        return item

    @patch(path="", dto=UpdateItemDTO, return_dto=ItemDTO)
    @inject
    async def patch_item(
        self, data: Item, unit_of_work: FromDishka[AbstractUnitOfWork]
    ) -> Item:
        item: Item | None = unit_of_work.items.get(data.id)
        if not item:
            logger.error(f"Item not found: {data.id}")
            raise HTTPException(status_code=404, detail="Item not found")
        updated_item: Item = unit_of_work.items.update(data)
        unit_of_work.commit()
        return updated_item

    @delete(path="/{item_id:int}")
    @inject
    async def delete_item(
        self, item_id: int, unit_of_work: FromDishka[AbstractUnitOfWork]
    ) -> None:
        item: Item | None = unit_of_work.items.get(item_id)
        if not item:
            logger.error(f"Item not found: {item_id}")
            raise HTTPException(status_code=404, detail="Item not found")
        unit_of_work.items.delete(item_id)
        unit_of_work.commit()
        return
