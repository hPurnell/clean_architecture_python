from app.shared.domain.errors import NotFoundError, PersistenceError


class JobNotFoundError(NotFoundError):
    def __init__(self, job_id: str | None) -> None:
        super().__init__(f"Job not found: {job_id}")
        self.job_id = job_id


class JobNotPersistedError(PersistenceError):
    """The repository declined to store the job."""
