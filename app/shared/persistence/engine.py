"""Engine and session-factory construction.

Nothing here runs at import time. The composition root builds a session factory
once, at application scope, and injects it into the unit of work, so that the
database connection is configurable per environment rather than being a
module-level singleton.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(
    database_url: str, isolation_level: str
) -> sessionmaker[Session]:
    engine = create_engine(database_url, isolation_level=isolation_level)
    return sessionmaker(bind=engine)
