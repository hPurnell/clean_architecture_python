from dishka.integrations.litestar import FromDishka, inject
from litestar.controller import Controller
from litestar.handlers.http_handlers.decorators import delete, patch, post
from litestar.status_codes import HTTP_202_ACCEPTED

from app.auth.controllers.guards import requires_role
from app.auth.domain.role import Role
from app.items.controllers.item_dto import NewItemDTO, UpdateItemDTO
from app.items.domain.item import Item
from app.items.service.item_command_dispatcher import ItemCommandDispatcher
from app.jobs.controllers.job_dto import JobDTO
from app.jobs.domain.job import Job


class ItemsCommandsDecoupledCtrl(Controller):
    """The same commands as /items, published instead of carried out."""

    path = "/items_decoupled"
    tags = ["Items Commands Decoupled"]
    return_dto = JobDTO

    @post(path="", dto=NewItemDTO, status_code=HTTP_202_ACCEPTED)
    @inject
    async def post_item(
        self,
        data: Item,
        item_command_dispatcher: FromDishka[ItemCommandDispatcher],
    ) -> Job:
        return await item_command_dispatcher.create_item(data)

    @patch(path="", dto=UpdateItemDTO, status_code=HTTP_202_ACCEPTED)
    @inject
    async def patch_item(
        self,
        data: Item,
        item_command_dispatcher: FromDishka[ItemCommandDispatcher],
    ) -> Job:
        return await item_command_dispatcher.update_item(data)

    @delete(
        path="/{item_id:int}",
        status_code=HTTP_202_ACCEPTED,
        guards=[requires_role(Role.ADMIN)],
    )
    @inject
    async def delete_item(
        self,
        item_id: int,
        item_command_dispatcher: FromDishka[ItemCommandDispatcher],
    ) -> Job:
        return await item_command_dispatcher.delete_item(item_id)
