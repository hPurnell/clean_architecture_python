import importlib
import pkgutil

import pytest

import app
from app.shared.persistence.entities import Base


@pytest.mark.unit
class TestEntities:
    def test_the_entities_module_registers_every_mapped_class(self):
        """No entity may be missing from app.shared.persistence.entities.

        Importing every module must reveal no table that importing the entities
        module alone did not, or a new aggregate silently never gets one.
        """
        declared = set(Base.metadata.tables)

        for module in pkgutil.walk_packages(app.__path__, prefix="app."):
            importlib.import_module(module.name)

        assert set(Base.metadata.tables) == declared
