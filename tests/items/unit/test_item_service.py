from datetime import datetime

import pytest

from app.items.db.fake_item_repository import FakeItemRepository
from app.items.domain.abstract_item_repository import AbstractItemRepository
from app.items.domain.errors import ItemIdRequiredError, ItemNotFoundError
from app.items.domain.item import Item
from app.items.service.item_service import ItemService
from app.shared.persistence.in_memory_unit_of_work import InMemoryUnitOfWork

STORED_DATE = datetime(2024, 12, 31, 13, 17, 29)


@pytest.fixture
def item_service() -> ItemService:
    return ItemService(
        InMemoryUnitOfWork({AbstractItemRepository: FakeItemRepository()})
    )


@pytest.fixture
def stored_item(item_service: ItemService) -> Item:
    return item_service.create_item(
        Item(
            value_str="keep",
            value_int=42,
            value_float=1.5,
            created_date=STORED_DATE,
            modified_date=STORED_DATE,
        )
    )


@pytest.mark.unit
class TestUpdateItem:
    def test_an_update_changes_the_fields_it_names(self, item_service, stored_item):
        updated_item = item_service.update_item(
            Item(id=stored_item.id, value_str="changed")
        )

        assert updated_item.value_str == "changed"

    def test_an_update_leaves_the_fields_it_does_not_name(
        self, item_service, stored_item
    ):
        """A PATCH says what changes, not what the item is."""
        updated_item = item_service.update_item(
            Item(id=stored_item.id, value_str="changed")
        )

        assert updated_item.value_int == stored_item.value_int
        assert updated_item.value_float == stored_item.value_float

    def test_what_the_update_returns_is_what_the_store_holds(
        self, item_service, stored_item
    ):
        # The repository's item, not a merge that only existed in the reply.
        item_service.update_item(Item(id=stored_item.id, value_str="changed"))

        reread_item = item_service.get_item(stored_item.id)

        assert reread_item.value_str == "changed"
        assert reread_item.value_int == stored_item.value_int
        assert reread_item.value_float == stored_item.value_float

    def test_an_update_keeps_when_the_item_was_created(self, item_service, stored_item):
        updated_item = item_service.update_item(
            Item(
                id=stored_item.id,
                value_str="changed",
                created_date=datetime(2000, 1, 1),
            )
        )

        assert updated_item.created_date == STORED_DATE

    def test_an_update_stamps_when_the_item_was_modified(
        self, item_service, stored_item
    ):
        # The repository writes modified_date explicitly, suppressing onupdate.
        updated_item = item_service.update_item(
            Item(id=stored_item.id, value_str="changed")
        )

        assert updated_item.modified_date is not None
        assert updated_item.modified_date > STORED_DATE

    def test_an_update_without_an_id_is_rejected(self, item_service, stored_item):
        with pytest.raises(ItemIdRequiredError):
            item_service.update_item(Item(value_str="changed"))

    def test_an_update_to_an_item_that_does_not_exist_is_rejected(self, item_service):
        with pytest.raises(ItemNotFoundError):
            item_service.update_item(Item(id=999999, value_str="changed"))
