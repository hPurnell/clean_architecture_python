from app.auth.domain import AbstractUserRepository, User
from app.auth.service.argon2_password_service import Argon2PasswordService

DEFAULT_PASSWORD = "password"
_PASSWORD_HASH = Argon2PasswordService().hash(DEFAULT_PASSWORD)


class FakeUserRepository(AbstractUserRepository):
    def __init__(self) -> None:
        self.collection = {
            "john.doe@example.com": User(
                id="1",
                name="John Doe",
                username="john.doe@example.com",
                password_hash=_PASSWORD_HASH,
            )
        }
        return

    def get_user(self, username: str) -> User | None:
        return self.collection.get(username)
