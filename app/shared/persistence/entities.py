"""Every mapped entity in the application, imported for its side effect.

A class only lands in ``Base.metadata`` once its module has been imported, and
Alembic compares that metadata against the database to work out what a
migration should contain. Nothing else imports every ``*_repository`` module,
so without this one place an entity that no request had happened to touch would
be invisible to ``alembic revision --autogenerate`` -- and would silently never
get a table.

Adding an aggregate means adding a line here. The entities test asserts that
this list covers every subclass of Base that the application defines, so a
forgotten import fails the suite rather than the next deployment.
"""

from app.items.db.item_repository import ItemEntity
from app.jobs.db.job_repository import JobEntity
from app.shared.persistence.base import Base

__all__ = ["Base", "ItemEntity", "JobEntity"]
