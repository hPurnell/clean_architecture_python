import logging
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

from app.jobs.domain.abstract_job_repository import AbstractJobRepository
from app.jobs.domain.errors import JobNotFoundError, JobNotPersistedError
from app.jobs.domain.job import Job
from app.shared.clock import utc_now
from app.shared.domain.errors import DomainError
from app.shared.domain.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, unit_of_work: AbstractUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    @property
    def _jobs(self) -> AbstractJobRepository:
        return self._unit_of_work.repository(AbstractJobRepository)

    def list_jobs(self) -> list[Job]:
        return self._jobs.get_all()

    def get_job(self, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return job

    def create_job(self, command: str) -> Job:
        """Record an accepted command and return the handle the client polls.

        The id is minted here because the command has to be published with it.
        """
        now = utc_now()
        created_job = self._jobs.create(
            Job(id=uuid4().hex, command=command, created_date=now, modified_date=now)
        )
        if created_job is None:
            raise JobNotPersistedError(f"Unable to create job for: {command}")
        self._unit_of_work.commit()
        return created_job

    def fail_job(self, job_id: str, error: str) -> Job:
        """Record that a job will never run, e.g. its command was never sent."""
        return self._record_failure(self.get_job(job_id), error)

    @contextmanager
    def track(self, job_id: str) -> Iterator[Job]:
        """Run the body as the work of ``job_id``, recording how it turns out.

        The body may set ``job.result``. A DomainError ends the job here, since
        redelivery would fail identically; anything else is re-raised to retry.
        """
        job = self.get_job(job_id)
        job.start(utc_now())
        self._save(job)
        try:
            yield job
        except DomainError as exc:
            logger.info("Job %s (%s) failed: %s", job.id, job.command, exc)
            self._record_failure(job, str(exc))
        except Exception as exc:
            logger.exception("Job %s (%s) failed unexpectedly", job.id, job.command)
            self._record_failure(job, f"{type(exc).__name__}: {exc}")
            raise
        else:
            job.succeed(utc_now())
            self._save(job)

    def _record_failure(self, job: Job, error: str) -> Job:
        # A transaction that failed part way through must not take the record
        # of its own failure down with it.
        self._unit_of_work.rollback()
        job.fail(error, utc_now())
        return self._save(job)

    def _save(self, job: Job) -> Job:
        # Only called on a job that has just moved, which stamped modified_date.
        updated_job = self._jobs.update(job)
        if updated_job is None:
            raise JobNotPersistedError(f"Unable to update job: {job.id}")
        self._unit_of_work.commit()
        return updated_job
