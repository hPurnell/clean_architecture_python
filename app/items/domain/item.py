from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True)
class Item:
    id: int | None = None
    value_str: str | None = None
    value_int: int | None = None
    value_float: float | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None
