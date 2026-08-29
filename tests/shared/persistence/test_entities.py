import importlib
import pkgutil

import pytest

import app
from app.shared.persistence.entities import Base


@pytest.mark.unit
class TestEntities:
    def test_the_entities_module_registers_every_mapped_class(self):
        """No entity may be missing from app.shared.persistence.entities.

        Alembic can only write a migration for a table it can see, and it sees
        the tables in Base.metadata -- which holds whatever happens to have
        been imported. Importing every module in the application must therefore
        reveal no table that importing the entities module alone did not.

        A new aggregate whose repository module is not listed there fails here,
        rather than by quietly never getting a table.
        """
        declared = set(Base.metadata.tables)

        for module in pkgutil.walk_packages(app.__path__, prefix="app."):
            importlib.import_module(module.name)

        assert set(Base.metadata.tables) == declared
