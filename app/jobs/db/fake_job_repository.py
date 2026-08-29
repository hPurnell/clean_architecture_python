from dataclasses import replace
from typing import Optional

from app.jobs.domain.abstract_job_repository import AbstractJobRepository
from app.jobs.domain.job import Job


class FakeJobRepository(AbstractJobRepository):
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}

    def create(self, obj: Job) -> Job:
        # Stored as a copy, so that a caller mutating the job it holds does not
        # silently change the stored one the way a real repository would not.
        self.jobs[obj.id] = replace(obj)
        return obj

    def get(self, obj_id: str) -> Optional[Job]:
        job = self.jobs.get(obj_id)
        return replace(job) if job else None

    def update(self, obj: Job) -> Optional[Job]:
        if obj.id in self.jobs:
            self.jobs[obj.id] = replace(obj)
            return obj
        return None

    def delete(self, obj_id: str) -> bool:
        if obj_id in self.jobs:
            del self.jobs[obj_id]
            return True
        return False

    def get_all(self) -> list[Job]:
        return [replace(job) for job in self.jobs.values()]
