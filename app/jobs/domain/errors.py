from typing import TYPE_CHECKING

from app.shared.domain.errors import ConflictError, NotFoundError, PersistenceError

if TYPE_CHECKING:
    # Annotations only: job.py imports this module, so a real import cycles.
    from app.jobs.domain.job import JobStatus


class JobNotFoundError(NotFoundError):
    def __init__(self, job_id: str | None) -> None:
        super().__init__(f"Job not found: {job_id}")
        self.job_id = job_id


class JobNotPersistedError(PersistenceError):
    """The repository declined to store the job."""


class InvalidJobTransitionError(ConflictError):
    """A job was asked to become something it cannot become from where it is."""

    def __init__(
        self, job_id: str, current: "JobStatus", requested: "JobStatus"
    ) -> None:
        super().__init__(
            f"Job {job_id} is {current.value} and cannot become {requested.value}."
        )
        self.job_id = job_id
        self.current = current
        self.requested = requested
