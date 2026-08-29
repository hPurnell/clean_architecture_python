"""Dispatching an item command, without a broker behind it."""

from typing import Any

import pytest

from app.items.db.fake_item_repository import FakeItemRepository
from app.items.domain.abstract_command_publisher import AbstractItemCommandPublisher
from app.items.domain.abstract_item_repository import AbstractItemRepository
from app.items.domain.item import Item
from app.items.service.item_command_dispatcher import ItemCommandDispatcher
from app.jobs.db.fake_job_repository import FakeJobRepository
from app.jobs.domain.abstract_job_repository import AbstractJobRepository
from app.jobs.domain.job import JobStatus
from app.jobs.service.job_service import JobService
from app.shared.persistence.in_memory_unit_of_work import InMemoryUnitOfWork


class RecordingPublisher(AbstractItemCommandPublisher):
    def __init__(self) -> None:
        self.published: list[tuple[Any, ...]] = []

    async def create_item(self, item: Item, job_id: str) -> None:
        self.published.append(("create_item", item, job_id))

    async def update_item(self, item: Item, job_id: str) -> None:
        self.published.append(("update_item", item, job_id))

    async def delete_item(self, item_id: int, job_id: str) -> None:
        self.published.append(("delete_item", item_id, job_id))


class UnreachablePublisher(AbstractItemCommandPublisher):
    async def create_item(self, item: Item, job_id: str) -> None:
        raise ConnectionError("no broker")

    async def update_item(self, item: Item, job_id: str) -> None:
        raise ConnectionError("no broker")

    async def delete_item(self, item_id: int, job_id: str) -> None:
        raise ConnectionError("no broker")


@pytest.fixture
def job_service() -> JobService:
    return JobService(
        InMemoryUnitOfWork(
            {
                AbstractJobRepository: FakeJobRepository(),
                AbstractItemRepository: FakeItemRepository(),
            }
        )
    )


@pytest.fixture
def publisher() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture
def dispatcher(
    publisher: RecordingPublisher, job_service: JobService
) -> ItemCommandDispatcher:
    return ItemCommandDispatcher(publisher, job_service)


@pytest.mark.unit
@pytest.mark.asyncio
class TestItemCommandDispatcher:
    async def test_create_item_publishes_the_job_id(
        self,
        dispatcher: ItemCommandDispatcher,
        publisher: RecordingPublisher,
        job_service: JobService,
    ):
        item = Item(value_str="Example String")

        job = await dispatcher.create_item(item)

        assert publisher.published == [("create_item", item, job.id)]
        assert job_service.get_job(job.id).status is JobStatus.PENDING

    async def test_update_item_publishes_the_job_id(
        self, dispatcher: ItemCommandDispatcher, publisher: RecordingPublisher
    ):
        item = Item(id=1, value_str="Updated String")

        job = await dispatcher.update_item(item)

        assert publisher.published == [("update_item", item, job.id)]
        assert job.command == "update_item"

    async def test_delete_item_publishes_the_job_id(
        self, dispatcher: ItemCommandDispatcher, publisher: RecordingPublisher
    ):
        job = await dispatcher.delete_item(1)

        assert publisher.published == [("delete_item", 1, job.id)]
        assert job.command == "delete_item"

    async def test_a_command_that_cannot_be_published_fails_its_job(
        self, job_service: JobService
    ):
        # Nothing will ever run the command, so the client must not be left
        # polling a job that stays pending for ever.
        dispatcher = ItemCommandDispatcher(UnreachablePublisher(), job_service)

        with pytest.raises(ConnectionError):
            await dispatcher.create_item(Item(value_str="Example String"))

        job = job_service.list_jobs()[0]
        assert job.status is JobStatus.FAILED
        assert job.error is not None and "no broker" in job.error
