from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "PENDING"  # recorded and published, not yet picked up
    RUNNING = "RUNNING"  # a subscriber has taken the command on
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


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
