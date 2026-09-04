# Every mapped entity, imported for its side effect: a class only lands in
# Base.metadata once its module has been imported, and that metadata is what
# alembic autogenerate compares against the database. Adding an aggregate means
# adding a line here, and the entities test fails if one is missing.
from app.auth.db.user_repository import UserEntity, UserRoleEntity
from app.items.db.item_repository import ItemEntity
from app.jobs.db.job_repository import JobEntity
from app.shared.persistence.base import Base

__all__ = ["Base", "ItemEntity", "JobEntity", "UserEntity", "UserRoleEntity"]
