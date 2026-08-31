from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.items.db.item_repository import ItemRepository
from app.items.domain.abstract_item_repository import AbstractItemRepository
from app.items.domain.item import Item
from app.items.service.item_service import ItemService
from app.shared.persistence.entities import Base
from app.shared.persistence.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def unit_of_work() -> Iterator[SqlAlchemyUnitOfWork]:
    """A unit of work over a real SQLAlchemy session.

    The fake repositories are dictionaries: they accept writes that the mapped
    columns reject, so a NOT NULL column written back as None reads as a
    successful update everywhere the fakes are used -- which, until this file,
    was everywhere. SQLite runs in-process and needs no server, so the real
    adapter can be exercised without the e2e mark.
    """
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with SqlAlchemyUnitOfWork(
        sessionmaker(bind=engine), {AbstractItemRepository: ItemRepository}
    ) as unit_of_work:
        yield unit_of_work


@pytest.mark.integration
class TestBaseRepository:
    def test_an_update_writes_every_field_it_is_handed(self, unit_of_work):
        """Which is why a caller's partial item cannot go straight to it.

        An Item carries None for whatever its caller left out, and this writes
        that None to the column. For a nullable column that is silent data
        loss; for created_date, which is NOT NULL, it is this.
        """
        items = unit_of_work.repository(AbstractItemRepository)
        created_item = items.create(Item(value_str="keep", value_int=42))
        unit_of_work.commit()

        with pytest.raises(IntegrityError):
            items.update(Item(id=created_item.id, value_str="changed"))


@pytest.mark.integration
class TestItemServiceAgainstADatabase:
    def test_a_partial_update_survives_the_mapped_columns(self, unit_of_work):
        # The same partial update as the unit tests make, against the adapter
        # that actually has constraints. It answered 500 before the service
        # merged onto the stored item.
        item_service = ItemService(unit_of_work)
        created_item = item_service.create_item(
            Item(value_str="keep", value_int=42, value_float=1.5)
        )

        updated_item = item_service.update_item(
            Item(id=created_item.id, value_str="changed")
        )

        assert updated_item.value_str == "changed"
        assert updated_item.value_int == 42
        assert updated_item.value_float == 1.5
        assert updated_item.created_date == created_item.created_date
        assert updated_item.modified_date is not None
