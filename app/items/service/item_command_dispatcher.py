from typing import Any, Coroutine

from app.items.domain.abstract_command_publisher import AbstractItemCommandPublisher
from app.items.domain.item import Item
from app.jobs.domain.job import Job
from app.jobs.service.job_service import JobService

CREATE_ITEM_COMMAND = "create_item"
UPDATE_ITEM_COMMAND = "update_item"
DELETE_ITEM_COMMAND = "delete_item"


class ItemCommandDispatcher:
    """Starts an item command as a background job and returns the job.

    The job is recorded before the command is published, so that a subscriber
    cannot reach it before it exists. Items may start jobs; the jobs context
    knows nothing about items.
    """

    def __init__(
        self,
        item_command_publisher: AbstractItemCommandPublisher,
        job_service: JobService,
    ) -> None:
        self._publisher = item_command_publisher
        self._job_service = job_service

    async def create_item(self, item: Item) -> Job:
        job = self._job_service.create_job(CREATE_ITEM_COMMAND)
        return await self._publish(job, self._publisher.create_item(item, job.id))

    async def update_item(self, item: Item) -> Job:
        job = self._job_service.create_job(UPDATE_ITEM_COMMAND)
        return await self._publish(job, self._publisher.update_item(item, job.id))

    async def delete_item(self, item_id: int) -> Job:
        job = self._job_service.create_job(DELETE_ITEM_COMMAND)
        return await self._publish(job, self._publisher.delete_item(item_id, job.id))

    async def _publish(self, job: Job, publication: Coroutine[Any, Any, None]) -> Job:
        try:
            await publication
        except Exception as exc:
            # Nothing will ever pick the command up, so the job is failed here
            # rather than left pending for a client that would poll it forever.
            self._job_service.fail_job(job.id, f"Unable to publish command: {exc}")
            raise
        return job
