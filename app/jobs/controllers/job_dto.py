from litestar.dto import DataclassDTO, DTOConfig

from app.jobs.domain.job import Job


class JobDTO(DataclassDTO[Job]):
    config = DTOConfig(rename_strategy="pascal")
