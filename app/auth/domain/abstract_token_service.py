from abc import ABC, abstractmethod

from app.auth.domain.token import Token


class AbstractTokenService(ABC):
    """Port for issuing and verifying access tokens."""

    @abstractmethod
    def encode(self, username: str) -> str: ...

    @abstractmethod
    def decode(self, encoded_token: str) -> Token:
        """Return the claims of ``encoded_token``, or raise InvalidTokenError."""
