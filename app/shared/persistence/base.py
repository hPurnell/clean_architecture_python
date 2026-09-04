from sqlalchemy.orm import DeclarativeBase


# One Base, so every table shares a single MetaData.
class Base(DeclarativeBase):
    pass
