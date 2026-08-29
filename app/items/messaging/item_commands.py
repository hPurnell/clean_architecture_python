from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any

from app.items.domain.errors import ItemIdRequiredError
from app.items.domain.item import Item

# The commands are deliberately not the Item entity: publishing the domain
# object would make every change to it a breaking change on the wire. Version 2
# added the job_id a command reports its outcome against, so these are not
# readable by a version 1 subscriber.
ITEM_COMMAND_SCHEMA_VERSION = 2


@dataclass(kw_only=True)
class ItemCommand:
    """What every item command carries, whatever it asks for."""

    job_id: str
    schema_version: int = ITEM_COMMAND_SCHEMA_VERSION


@dataclass(kw_only=True)
class ItemValues:
    """The part of an item a caller supplies. Never published on its own."""

    value_str: str | None = None
    value_int: int | None = None
    value_float: float | None = None


@dataclass(kw_only=True)
class CreateItemCommand(ItemCommand, ItemValues):
    pass


@dataclass(kw_only=True)
class UpdateItemCommand(ItemCommand, ItemValues):
    id: int
    created_date: datetime | None = None
    modified_date: datetime | None = None


@dataclass(kw_only=True)
class DeleteItemCommand(ItemCommand):
    id: int


def _values_of(source: Item | ItemValues) -> dict[str, Any]:
    """Read the fields ``ItemValues`` names off a domain item or a command.

    The two shapes agree on these names by design, and this is the one place
    that relies on it: renaming a value on either side without renaming it on
    the other has to be handled here.
    """
    return {field.name: getattr(source, field.name) for field in fields(ItemValues)}


def to_create_command(item: Item, job_id: str) -> CreateItemCommand:
    return CreateItemCommand(job_id=job_id, **_values_of(item))


def to_update_command(item: Item, job_id: str) -> UpdateItemCommand:
    if item.id is None:
        raise ItemIdRequiredError()
    return UpdateItemCommand(
        job_id=job_id,
        id=item.id,
        created_date=item.created_date,
        modified_date=item.modified_date,
        **_values_of(item),
    )


def to_delete_command(item_id: int, job_id: str) -> DeleteItemCommand:
    return DeleteItemCommand(job_id=job_id, id=item_id)


def from_create_command(command: CreateItemCommand) -> Item:
    return Item(**_values_of(command))


def from_update_command(command: UpdateItemCommand) -> Item:
    return Item(
        id=command.id,
        created_date=command.created_date,
        modified_date=command.modified_date,
        **_values_of(command),
    )
