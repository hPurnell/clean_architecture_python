import json
from dataclasses import fields
from datetime import datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from app.items.domain.errors import ItemIdRequiredError
from app.items.domain.item import Item
from app.items.messaging.item_commands import (
    ITEM_COMMAND_SCHEMA_VERSION,
    CreateItemCommand,
    DeleteItemCommand,
    ItemValues,
    UpdateItemCommand,
    from_create_command,
    from_update_command,
    to_create_command,
    to_delete_command,
    to_update_command,
)

JOB_ID = "9f2c1d8e4b7a4b0f8a1c6d3e5f7a9b2c"


@pytest.fixture
def item() -> Item:
    return Item(
        id=7,
        value_str="Example String",
        value_int=42,
        value_float=123.45,
        created_date=datetime(2024, 12, 31, 13, 17, 29),
        modified_date=datetime(2024, 12, 31, 13, 45, 10),
    )


@pytest.mark.unit
class TestItemCommands:
    def test_every_command_carries_the_job_and_the_schema_version(self, item: Item):
        assert item.id is not None
        commands = [
            to_create_command(item, JOB_ID),
            to_update_command(item, JOB_ID),
            to_delete_command(item.id, JOB_ID),
        ]

        for command in commands:
            assert command.job_id == JOB_ID
            assert command.schema_version == ITEM_COMMAND_SCHEMA_VERSION

    def test_a_create_command_carries_the_values_and_nothing_else(self, item: Item):
        command = to_create_command(item, JOB_ID)

        assert command.value_str == item.value_str
        assert command.value_int == item.value_int
        assert command.value_float == item.value_float
        # An id and the dates are the store's to assign, not the caller's.
        assert not hasattr(command, "id")
        assert not hasattr(command, "created_date")

    def test_a_create_command_maps_back_to_an_unidentified_item(self, item: Item):
        mapped_item = from_create_command(to_create_command(item, JOB_ID))

        assert mapped_item == Item(
            value_str=item.value_str,
            value_int=item.value_int,
            value_float=item.value_float,
        )

    def test_an_update_command_survives_the_round_trip(self, item: Item):
        assert from_update_command(to_update_command(item, JOB_ID)) == item

    def test_an_update_command_needs_an_item_id(self, item: Item):
        item.id = None

        with pytest.raises(ItemIdRequiredError):
            to_update_command(item, JOB_ID)

    def test_a_delete_command_carries_only_the_id(self):
        command = to_delete_command(7, JOB_ID)

        assert command.id == 7
        assert {field.name for field in fields(command)} == {
            "id",
            "job_id",
            "schema_version",
        }

    def test_the_commands_share_one_definition_of_an_item_s_values(self):
        # The point of the composition: a value added to ItemValues reaches
        # every command that carries item data, and nothing else.
        value_names = {field.name for field in fields(ItemValues)}

        assert value_names <= {field.name for field in fields(CreateItemCommand)}
        assert value_names <= {field.name for field in fields(UpdateItemCommand)}
        assert value_names.isdisjoint(
            {field.name for field in fields(DeleteItemCommand)}
        )

    @pytest.mark.parametrize(
        "command",
        [
            CreateItemCommand(job_id=JOB_ID, value_str="s", value_int=1),
            UpdateItemCommand(job_id=JOB_ID, id=3, created_date=datetime(2025, 1, 1)),
            DeleteItemCommand(job_id=JOB_ID, id=3),
        ],
    )
    def test_a_command_survives_the_broker(self, command):
        # The subscriber receives JSON and pydantic rebuilds the dataclass from
        # it, so composed commands have to decode as flatly as written-out ones.
        adapter = TypeAdapter(type(command))

        decoded = adapter.validate_python(json.loads(adapter.dump_json(command)))

        assert decoded == command

    def test_a_command_without_a_job_is_rejected(self):
        # Version 1 messages predate the job id and cannot be run.
        with pytest.raises(ValidationError):
            TypeAdapter(DeleteItemCommand).validate_python(
                {"id": 3, "schema_version": 1}
            )
