from dataclasses import dataclass, field
from datetime import datetime

from app.auth.domain.role import Role


def normalise_username(username: str) -> str:
    """A username is an email address, so case and padding are not identity."""
    return username.strip().lower()


@dataclass(kw_only=True)
class User:
    id: str
    name: str
    username: str
    password_hash: str
    roles: frozenset[Role] = field(default_factory=frozenset)
    created_date: datetime | None = None
    modified_date: datetime | None = None
