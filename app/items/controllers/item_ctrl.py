from dishka.integrations.litestar import FromDishka, inject
from litestar.controller import Controller
from litestar.handlers.http_handlers.decorators import delete, get, patch, post

from app.items.controllers.item_dto import ItemDTO, NewItemDTO, UpdateItemDTO
from app.items.domain.item import Item
from app.items.service.item_service import ItemService


class ItemController(Controller):
    path = "/items"
    tags = ["Items"]

    @get(path="", return_dto=ItemDTO)
    @inject
    async def get_items(self, item_service: FromDishka[ItemService]) -> list[Item]:
        return item_service.list_items()

    @get(path="/{item_id:int}", return_dto=ItemDTO)
    @inject
    async def get_item(
        self, item_id: int, item_service: FromDishka[ItemService]
    ) -> Item:
        return item_service.get_item(item_id)

    @post(path="", dto=NewItemDTO, return_dto=ItemDTO)
    @inject
    async def post_item(
        self, data: Item, item_service: FromDishka[ItemService]
    ) -> Item:
        return item_service.create_item(data)

    @patch(path="", dto=UpdateItemDTO, return_dto=ItemDTO)
    @inject
    async def patch_item(
        self, data: Item, item_service: FromDishka[ItemService]
    ) -> Item:
        return item_service.update_item(data)

    @delete(path="/{item_id:int}")
    @inject
    async def delete_item(
        self, item_id: int, item_service: FromDishka[ItemService]
    ) -> None:
        item_service.delete_item(item_id)
