from abc import ABC, abstractmethod

from app.auth.domain.token import Token


class AbstractAuthService(ABC):
    """Port for exchanging credentials for a token, and a token for its claims."""

    @abstractmethod
    def login(self, username: str, password: str) -> str:
        """Return an encoded token, or raise InvalidCredentialsError.

        An unknown user and a wrong password are not distinguished: telling
        them apart reveals which usernames exist.
        """

    @abstractmethod
    def verify(self, encoded_token: str) -> Token:
        """Return the claims of ``encoded_token``, or raise InvalidTokenError."""
