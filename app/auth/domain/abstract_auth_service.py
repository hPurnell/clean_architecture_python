from abc import ABC, abstractmethod

from app.auth.domain.token import Token
from app.auth.domain.user import User


class AbstractAuthService(ABC):
    """Port for registering users and exchanging credentials for a token."""

    @abstractmethod
    def register(self, name: str, username: str, password: str) -> User:
        """Store a new user and return it, without their password.

        Raises UsernameTakenError or WeakPasswordError.
        """

    @abstractmethod
    def login(self, username: str, password: str) -> str:
        """Return an encoded token, or raise InvalidCredentialsError.

        An unknown user and a wrong password are not distinguished, in the
        answer or in the time taken: either tells a caller which usernames
        exist.
        """

    @abstractmethod
    def change_password(
        self, username: str, current_password: str, new_password: str
    ) -> None:
        """Replace a user's password, given the one it is replacing."""

    @abstractmethod
    def verify(self, encoded_token: str) -> Token:
        """Return the claims of ``encoded_token``, or raise InvalidTokenError."""
