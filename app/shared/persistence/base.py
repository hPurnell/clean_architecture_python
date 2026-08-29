"""The single declarative base for the whole application.

Every ORM entity must inherit from this ``Base`` so that all tables share one
``MetaData``. A per-module ``declarative_base()`` would give each table its own
disconnected registry, which breaks ``create_all``/``drop_all`` and string-named
``ForeignKey`` resolution across modules.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
