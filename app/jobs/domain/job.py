from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping

from app.jobs.domain.errors import InvalidJobTransitionError


class JobStatus(str, Enum):
    PENDING = "PENDING"  # recorded and published, not yet picked up
    RUNNING = "RUNNING"  # a subscriber has taken the command on
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


# Which statuses a job may reach from the one it holds. Retries are the
# broker's, so FAILED -> RUNNING and RUNNING -> RUNNING are redeliveries rather
# than mistakes. SUCCEEDED is terminal: a caller has already polled that result.
ALLOWED_TRANSITIONS: Mapping[JobStatus, frozenset[JobStatus]] = {
    JobStatus.PENDING: frozenset({JobStatus.RUNNING, JobStatus.FAILED}),
    JobStatus.RUNNING: frozenset(
        {JobStatus.RUNNING, JobStatus.SUCCEEDED, JobStatus.FAILED}
    ),
    JobStatus.FAILED: frozenset({JobStatus.RUNNING}),
    JobStatus.SUCCEEDED: frozenset(),
}


@dataclass(kw_only=True)
class Job:
    id: str
    command: str
    status: JobStatus = JobStatus.PENDING
    # The identifier of whatever the command produced or affected, as a string.
    # What it identifies is the caller's business: for an item command it is an
    # item id, and the client follows it to /items/{result}.
    result: str | None = None
    error: str | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None

    def start(self, at: datetime) -> None:
        """Take the command on, clearing any error from a previous attempt."""
        self._move_to(JobStatus.RUNNING, at)
        self.error = None

    def succeed(self, at: datetime) -> None:
        """Record that the command was carried out; the work sets ``result``."""
        self._move_to(JobStatus.SUCCEEDED, at)

    def fail(self, error: str, at: datetime) -> None:
        """Record that the command did not happen, and why."""
        self._move_to(JobStatus.FAILED, at)
        self.error = error

    def _move_to(self, status: JobStatus, at: datetime) -> None:
        if status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidJobTransitionError(self.id, self.status, status)
        self.status = status
        # The repository writes every field, suppressing the column's onupdate.
        self.modified_date = at
