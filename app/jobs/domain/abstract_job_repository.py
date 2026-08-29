from app.jobs.domain.job import Job
from app.shared.domain.repository import AbstractRepository


class AbstractJobRepository(AbstractRepository[Job, str]):
    pass
