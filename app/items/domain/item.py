from dataclasses import dataclass, fields, replace
from datetime import datetime

# Written by the store, never taken from a caller's update.
SERVER_OWNED_FIELDS = frozenset({"id", "created_date", "modified_date"})


@dataclass(kw_only=True)
class Item:
    id: int | None = None
    value_str: str | None = None
    value_int: int | None = None
    value_float: float | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None

    def with_changes_from(self, changes: "Item", modified_at: datetime) -> "Item":
        """Return this item as ``changes`` asks it to become.

        A field left as None is one the caller said nothing about, so this
        item's value survives it.
        """
        changed_fields = {
            field.name: getattr(changes, field.name)
            for field in fields(changes)
            if field.name not in SERVER_OWNED_FIELDS
            and getattr(changes, field.name) is not None
        }
        return replace(self, **changed_fields, modified_date=modified_at)
