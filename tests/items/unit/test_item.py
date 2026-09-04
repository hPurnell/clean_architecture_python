from datetime import datetime

import pytest

from app.items.domain.item import Item

STORED_DATE = datetime(2024, 12, 31, 13, 17, 29)
MODIFIED_AT = datetime(2025, 1, 1, 9, 0, 0)


@pytest.fixture
def stored_item() -> Item:
    return Item(
        id=7,
        value_str="keep",
        value_int=42,
        value_float=1.5,
        created_date=STORED_DATE,
        modified_date=STORED_DATE,
    )


@pytest.mark.unit
class TestWithChangesFrom:
    def test_a_named_field_changes(self, stored_item: Item):
        changed = stored_item.with_changes_from(Item(value_str="changed"), MODIFIED_AT)

        assert changed.value_str == "changed"

    def test_a_field_that_is_not_named_survives(self, stored_item: Item):
        changed = stored_item.with_changes_from(Item(value_str="changed"), MODIFIED_AT)

        assert changed.value_int == 42
        assert changed.value_float == 1.5

    def test_the_stored_item_is_left_as_it_was(self, stored_item: Item):
        # A copy, so nothing is half-changed if the write that follows fails.
        stored_item.with_changes_from(Item(value_str="changed"), MODIFIED_AT)

        assert stored_item.value_str == "keep"

    def test_the_id_is_never_taken_from_the_changes(self, stored_item: Item):
        changed = stored_item.with_changes_from(
            Item(id=999, value_str="changed"), MODIFIED_AT
        )

        assert changed.id == 7

    def test_the_creation_time_is_never_taken_from_the_changes(self, stored_item: Item):
        changed = stored_item.with_changes_from(
            Item(created_date=datetime(2000, 1, 1)), MODIFIED_AT
        )

        assert changed.created_date == STORED_DATE

    def test_the_modification_time_is_the_one_given(self, stored_item: Item):
        changed = stored_item.with_changes_from(
            Item(modified_date=datetime(2000, 1, 1)), MODIFIED_AT
        )

        assert changed.modified_date == MODIFIED_AT

    def test_changes_that_name_nothing_only_move_the_clock(self, stored_item: Item):
        changed = stored_item.with_changes_from(Item(), MODIFIED_AT)

        assert changed == Item(
            id=7,
            value_str="keep",
            value_int=42,
            value_float=1.5,
            created_date=STORED_DATE,
            modified_date=MODIFIED_AT,
        )
