from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


# Called once by the composition root, never at import time, so the database
# connection stays configurable per environment instead of being a singleton.
def create_session_factory(
    database_url: str, isolation_level: str
) -> sessionmaker[Session]:
    engine = create_engine(database_url, isolation_level=isolation_level)
    return sessionmaker(bind=engine)
