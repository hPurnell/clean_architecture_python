from dataclasses import dataclass
from datetime import datetime

from app.items.domain.errors import ItemIdRequiredError
from app.items.domain.item import Item

ITEM_COMMAND_SCHEMA_VERSION = 1


@dataclass(kw_only=True)
class ItemCommand:
    """What every item command carries, whatever it asks for."""

    job_id: str
    schema_version: int = ITEM_COMMAND_SCHEMA_VERSION


@dataclass(kw_only=True)
class CreateItemCommand(ItemCommand):
    value_str: str | None = None
    value_int: int | None = None
    value_float: float | None = None


@dataclass(kw_only=True)
class UpdateItemCommand(ItemCommand):
    id: int
    value_str: str | None = None
    value_int: int | None = None
    value_float: float | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None


@dataclass(kw_only=True)
class DeleteItemCommand(ItemCommand):
    id: int


def to_create_command(item: Item, job_id: str) -> CreateItemCommand:
    return CreateItemCommand(
        job_id=job_id,
        value_str=item.value_str,
        value_int=item.value_int,
        value_float=item.value_float,
    )


def to_update_command(item: Item, job_id: str) -> UpdateItemCommand:
    if item.id is None:
        raise ItemIdRequiredError()
    return UpdateItemCommand(
        job_id=job_id,
        id=item.id,
        value_str=item.value_str,
        value_int=item.value_int,
        value_float=item.value_float,
        created_date=item.created_date,
        modified_date=item.modified_date,
    )


def to_delete_command(item_id: int, job_id: str) -> DeleteItemCommand:
    return DeleteItemCommand(job_id=job_id, id=item_id)


def from_create_command(command: CreateItemCommand) -> Item:
    return Item(
        value_str=command.value_str,
        value_int=command.value_int,
        value_float=command.value_float,
    )


def from_update_command(command: UpdateItemCommand) -> Item:
    return Item(
        id=command.id,
        value_str=command.value_str,
        value_int=command.value_int,
        value_float=command.value_float,
        created_date=command.created_date,
        modified_date=command.modified_date,
    )
