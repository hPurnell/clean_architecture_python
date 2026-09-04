from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


# Called by the composition root, never at import time.
def create_session_factory(
    database_url: str, isolation_level: str
) -> sessionmaker[Session]:
    engine = create_engine(database_url, isolation_level=isolation_level)
    return sessionmaker(bind=engine)
