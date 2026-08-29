import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Session

from app.jobs.domain.abstract_job_repository import AbstractJobRepository
from app.jobs.domain.job import Job, JobStatus
from app.shared.persistence.base import Base
from app.shared.persistence.repository import BaseRepository


class JobEntity(Base):
    __tablename__ = "jobs"

    # Not autoincremented: the id is minted by the service before the command
    # that carries it is published.
    id = Column(String(32), primary_key=True)
    command = Column(String(100), nullable=False)
    status = Column(SqlEnum(JobStatus), nullable=False)  # type: Column[JobStatus]
    result = Column(String(255), nullable=True)
    error = Column(String(1000), nullable=True)
    created_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    modified_date = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class JobRepository(BaseRepository[JobEntity, Job], AbstractJobRepository):
    def __init__(self, session: Session):
        super().__init__(session, JobEntity, Job)
