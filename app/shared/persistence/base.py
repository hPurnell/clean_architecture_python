from sqlalchemy.orm import DeclarativeBase


# Every ORM entity must inherit from this one Base so that all tables share a
# single MetaData. A per-module declarative_base() gives each table its own
# registry, which breaks create_all/drop_all and cross-module ForeignKey strings.
class Base(DeclarativeBase):
    pass
