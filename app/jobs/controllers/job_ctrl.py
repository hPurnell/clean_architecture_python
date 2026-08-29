from dishka.integrations.litestar import FromDishka, inject
from litestar.controller import Controller
from litestar.handlers.http_handlers.decorators import get

from app.jobs.controllers.job_dto import JobDTO
from app.jobs.domain.job import Job
from app.jobs.service.job_service import JobService


class JobController(Controller):
    path = "/jobs"
    tags = ["Jobs"]
    return_dto = JobDTO

    @get(path="")
    @inject
    async def get_jobs(self, job_service: FromDishka[JobService]) -> list[Job]:
        return job_service.list_jobs()

    @get(path="/{job_id:str}")
    @inject
    async def get_job(self, job_id: str, job_service: FromDishka[JobService]) -> Job:
        return job_service.get_job(job_id)
