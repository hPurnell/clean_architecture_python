"""Create the database tables defined by the ORM entities.

Usage:
    python create_tables.py             # create missing tables
    python create_tables.py --drop      # drop every table first, then create
    python create_tables.py --drop --yes  # same, without the confirmation prompt

``--drop`` destroys all data in the target database.
"""

import argparse
import sys

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.config import config

# Importing the entity modules registers their tables on Base.metadata. Every
# new table module must be imported here for it to be created.
from app.items.db import item_repository  # noqa: F401
from app.jobs.db import job_repository  # noqa: F401
from app.shared.persistence.base import Base


def create_tables(drop_existing: bool = False) -> None:
    engine = create_engine(config.DATABASE_URL)
    if drop_existing:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def confirm_drop(database_url: str) -> bool:
    safe_url = make_url(database_url).render_as_string(hide_password=True)
    print(f"This will DROP every table in: {safe_url}")
    print("All data in that database will be lost.")
    return input("Type 'drop' to continue: ").strip() == "drop"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating them. Destroys all data.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt for --drop.",
    )
    args = parser.parse_args()

    if args.drop and not args.yes and not confirm_drop(config.DATABASE_URL):
        print("Aborted.")
        return 1

    create_tables(drop_existing=args.drop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
