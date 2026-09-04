from abc import ABC, abstractmethod

from app.auth.domain.user import User


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_user(self, username: str) -> User | None:
        """Return the user stored under this exact username, or None."""

    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def update(self, user: User) -> User | None: ...
