import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4

from app.jobs.domain.abstract_job_repository import AbstractJobRepository
from app.jobs.domain.errors import JobNotFoundError, JobNotPersistedError
from app.jobs.domain.job import Job, JobStatus
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

        The id is generated here rather than by the database: the command that
        carries it has to be published with it, so it must exist before any
        worker could possibly see the job.
        """
        now = datetime.utcnow()
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

        The body may set ``job.result`` to the identifier of whatever it
        produced; the job is stored as SUCCEEDED when the body returns, and as
        FAILED, with the error message, when it raises.

        A ``DomainError`` ends the job here: redelivering the command would
        fail in exactly the same way, so the job record becomes the report and
        the caller acknowledges the message. Any other exception is re-raised
        once the failure has been recorded, on the assumption that it may be
        transient and the command is worth retrying.
        """
        job = self.get_job(job_id)
        job.status = JobStatus.RUNNING
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
            job.status = JobStatus.SUCCEEDED
            self._save(job)

    def _record_failure(self, job: Job, error: str) -> Job:
        # Discard whatever the work left uncommitted: a transaction that failed
        # part way through must not be allowed to take the record of its own
        # failure down with it. Work the command committed before it failed is
        # already durable and is not this method's to undo.
        self._unit_of_work.rollback()
        job.status = JobStatus.FAILED
        job.error = error
        return self._save(job)

    def _save(self, job: Job) -> Job:
        # Stamped here rather than left to the column's ``onupdate``: the
        # repository writes every field explicitly, which suppresses it, and
        # the in-memory repository has no clock of its own at all. A client
        # polling a job needs to see this move.
        job.modified_date = datetime.utcnow()
        updated_job = self._jobs.update(job)
        if updated_job is None:
            raise JobNotPersistedError(f"Unable to update job: {job.id}")
        self._unit_of_work.commit()
        return updated_job
