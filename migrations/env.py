from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import config as app_config

# Importing this module is what populates Base.metadata: see its docstring.
from app.shared.persistence.entities import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# What autogenerate compares the database against.
target_metadata = Base.metadata


def _database_url() -> str:
    """The URL to migrate, from the same configuration the application uses.

    Deliberately not stored in alembic.ini: the connection string carries a
    password and differs per environment, and a second copy of it is a second
    thing to get wrong. ``-x url=...`` overrides it for a one-off run against
    another database.
    """
    override = context.get_x_argument(as_dictionary=True).get("url")
    return str(override or app_config.DATABASE_URL)


def run_migrations_offline() -> None:
    """Emit the migration as SQL on stdout instead of running it.

    ``alembic upgrade head --sql`` produces a script a DBA can read and apply
    by hand, which is how a change reaches a database this process has no
    credentials for.
    """
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Off by default, so a column whose type or default changed would
            # otherwise autogenerate an empty migration and look like no drift.
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
