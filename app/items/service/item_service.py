from dataclasses import fields, replace
from datetime import datetime, timezone

from app.items.domain.abstract_item_repository import AbstractItemRepository
from app.items.domain.errors import (
    ItemIdRequiredError,
    ItemNotFoundError,
    ItemNotPersistedError,
)
from app.items.domain.item import Item
from app.shared.domain.unit_of_work import AbstractUnitOfWork

# Written by the store rather than by whoever asked for the change: an update
# says what should become true of an item, and when it was created is not that.
SERVER_OWNED_FIELDS = frozenset({"id", "created_date", "modified_date"})


class ItemService:
    def __init__(self, unit_of_work: AbstractUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    @property
    def _items(self) -> AbstractItemRepository:
        return self._unit_of_work.repository(AbstractItemRepository)

    def list_items(self) -> list[Item]:
        return self._items.get_all()

    def get_item(self, item_id: int) -> Item:
        item = self._items.get(item_id)
        if item is None:
            raise ItemNotFoundError(item_id)
        return item

    def create_item(self, item: Item) -> Item:
        created_item = self._items.create(item)
        if created_item is None:
            raise ItemNotPersistedError(f"Unable to create item: {item}")
        self._unit_of_work.commit()
        return created_item

    def update_item(self, item: Item) -> Item:
        """Apply the fields ``item`` carries to the stored item of that id.

        A field left as ``None`` is one the caller said nothing about, so the
        stored value survives it: a PATCH naming two fields must not blank the
        four it does not mention. The repository writes every column it is
        handed, so the merge has to happen before it gets there -- against a
        real database, writing the omitted ``created_date`` back as NULL is
        not silent data loss but an outright constraint violation.

        ``modified_date`` is stamped here rather than left to the column's
        ``onupdate``, which that same write-everything behaviour suppresses.
        """
        if item.id is None:
            raise ItemIdRequiredError()

        stored_item = self._items.get(item.id)
        if stored_item is None:
            raise ItemNotFoundError(item.id)

        changes = {
            field.name: getattr(item, field.name)
            for field in fields(item)
            if field.name not in SERVER_OWNED_FIELDS
            and getattr(item, field.name) is not None
        }
        merged_item = replace(stored_item, **changes)
        # Naive UTC, which is how the DateTime columns store it.
        merged_item.modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

        updated_item = self._items.update(merged_item)
        if updated_item is None:
            raise ItemNotPersistedError(f"Unable to update item: {item}")
        self._unit_of_work.commit()
        return updated_item

    def delete_item(self, item_id: int) -> None:
        if not self._items.delete(item_id):
            raise ItemNotFoundError(item_id)
        self._unit_of_work.commit()
