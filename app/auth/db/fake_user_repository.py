from dataclasses import replace

from app.auth.domain.abstract_user_repository import AbstractUserRepository
from app.auth.domain.role import Role
from app.auth.domain.user import User
from app.auth.service.argon2_password_service import Argon2PasswordService

DEFAULT_USERNAME = "john.doe@example.com"
PLAIN_USERNAME = "jane.roe@example.com"
DEFAULT_PASSWORD = "password"
_PASSWORD_HASH = Argon2PasswordService().hash(DEFAULT_PASSWORD)


class FakeUserRepository(AbstractUserRepository):
    def __init__(self) -> None:
        # Two seeded users, so the tests have both sides of a role check.
        self.collection: dict[str, User] = {
            DEFAULT_USERNAME: User(
                id="1",
                name="John Doe",
                username=DEFAULT_USERNAME,
                password_hash=_PASSWORD_HASH,
                roles=frozenset({Role.ADMIN, Role.USER}),
            ),
            PLAIN_USERNAME: User(
                id="2",
                name="Jane Roe",
                username=PLAIN_USERNAME,
                password_hash=_PASSWORD_HASH,
                roles=frozenset({Role.USER}),
            ),
        }

    def get_user(self, username: str) -> User | None:
        user = self.collection.get(username)
        return replace(user) if user else None

    def add(self, user: User) -> User:
        self.collection[user.username] = replace(user)
        return user

    def update(self, user: User) -> User | None:
        if self.collection.get(user.username) is None:
            return None
        self.collection[user.username] = replace(user)
        return user
