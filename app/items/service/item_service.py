"""Item use cases.

Every rule about items lives here: what counts as "not found", when a change is
committed, what happens when the repository refuses a write. Both the HTTP
controller and the message subscriber call these methods, so the two transports
cannot drift apart, and neither of them needs to know about transactions.
"""

from app.items.domain.abstract_item_repository import AbstractItemRepository
from app.items.domain.errors import (
    ItemIdRequiredError,
    ItemNotFoundError,
    ItemNotPersistedError,
)
from app.items.domain.item import Item
from app.shared.domain.unit_of_work import AbstractUnitOfWork


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
        if item.id is None:
            raise ItemIdRequiredError()
        if self._items.get(item.id) is None:
            raise ItemNotFoundError(item.id)
        updated_item = self._items.update(item)
        if updated_item is None:
            raise ItemNotPersistedError(f"Unable to update item: {item}")
        self._unit_of_work.commit()
        return updated_item

    def delete_item(self, item_id: int) -> None:
        if not self._items.delete(item_id):
            raise ItemNotFoundError(item_id)
        self._unit_of_work.commit()
