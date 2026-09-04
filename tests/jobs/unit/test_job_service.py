import pytest

from app.items.db.fake_item_repository import FakeItemRepository
from app.items.domain.abstract_item_repository import AbstractItemRepository
from app.items.domain.errors import ItemNotFoundError
from app.items.domain.item import Item
from app.items.service.item_service import ItemService
from app.jobs.db.fake_job_repository import FakeJobRepository
from app.jobs.domain.abstract_job_repository import AbstractJobRepository
from app.jobs.domain.errors import JobNotFoundError
from app.jobs.domain.job import JobStatus
from app.jobs.service.job_service import JobService
from app.shared.persistence.in_memory_unit_of_work import InMemoryUnitOfWork


@pytest.fixture
def unit_of_work() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork(
        {
            AbstractJobRepository: FakeJobRepository(),
            AbstractItemRepository: FakeItemRepository(),
        }
    )


@pytest.fixture
def job_service(unit_of_work: InMemoryUnitOfWork) -> JobService:
    return JobService(unit_of_work)


@pytest.fixture
def item_service(unit_of_work: InMemoryUnitOfWork) -> ItemService:
    return ItemService(unit_of_work)


@pytest.mark.unit
class TestJobService:
    def test_a_new_job_is_pending(self, job_service: JobService):
        job = job_service.create_job("create_item")

        assert job.status is JobStatus.PENDING
        assert job.result is None
        assert job.error is None
        assert job_service.get_job(job.id) == job

    def test_each_job_gets_its_own_id(self, job_service: JobService):
        first = job_service.create_job("create_item")
        second = job_service.create_job("create_item")

        assert first.id != second.id

    def test_get_unknown_job(self, job_service: JobService):
        with pytest.raises(JobNotFoundError):
            job_service.get_job("no-such-job")

    def test_job_is_running_while_the_work_runs(self, job_service: JobService):
        job = job_service.create_job("create_item")

        with job_service.track(job.id):
            assert job_service.get_job(job.id).status is JobStatus.RUNNING

    def test_completed_work_reports_its_result(
        self, job_service: JobService, item_service: ItemService
    ):
        job = job_service.create_job("create_item")

        with job_service.track(job.id) as tracked:
            created_item = item_service.create_item(Item(value_str="Example String"))
            tracked.result = str(created_item.id)

        finished_job = job_service.get_job(job.id)
        assert finished_job.status is JobStatus.SUCCEEDED
        assert finished_job.result == str(created_item.id)
        assert finished_job.error is None
        assert finished_job.created_date is not None
        assert finished_job.modified_date is not None
        assert finished_job.modified_date > finished_job.created_date

    def test_a_domain_error_ends_the_job_rather_than_the_message(
        self, job_service: JobService, item_service: ItemService
    ):
        # Swallowed on purpose: a redelivery would fail identically.
        job = job_service.create_job("delete_item")

        with job_service.track(job.id):
            item_service.delete_item(999999)

        failed_job = job_service.get_job(job.id)
        assert failed_job.status is JobStatus.FAILED
        assert failed_job.error == str(ItemNotFoundError(999999))

    def test_an_unexpected_error_is_recorded_and_re_raised(
        self, job_service: JobService
    ):
        # Re-raised so the broker can redeliver a command that may yet succeed.
        job = job_service.create_job("update_item")

        with pytest.raises(RuntimeError):
            with job_service.track(job.id):
                raise RuntimeError("the connection dropped")

        failed_job = job_service.get_job(job.id)
        assert failed_job.status is JobStatus.FAILED
        assert failed_job.error == "RuntimeError: the connection dropped"

    def test_a_redelivered_command_can_run_a_failed_job_again(
        self, job_service: JobService
    ):
        # The job that comes back from a redelivery is FAILED, so tracking it
        # again has to be allowed or the retry could never happen.
        job = job_service.create_job("update_item")
        with pytest.raises(RuntimeError):
            with job_service.track(job.id):
                raise RuntimeError("the connection dropped")

        with job_service.track(job.id) as retried:
            retried.result = "7"

        finished_job = job_service.get_job(job.id)
        assert finished_job.status is JobStatus.SUCCEEDED
        assert finished_job.result == "7"
        # The first attempt's error is not still hanging off a job that worked.
        assert finished_job.error is None

    def test_a_job_that_was_never_published_is_failed(self, job_service: JobService):
        job = job_service.create_job("create_item")

        job_service.fail_job(job.id, "Unable to publish command: no broker")

        assert job_service.get_job(job.id).status is JobStatus.FAILED

    def test_list_jobs(self, job_service: JobService):
        ids = {job_service.create_job("create_item").id for _ in range(3)}

        assert {job.id for job in job_service.list_jobs()} == ids
