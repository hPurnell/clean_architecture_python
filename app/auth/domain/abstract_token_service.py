from abc import ABC, abstractmethod
from collections.abc import Collection

from app.auth.domain.role import Role
from app.auth.domain.token import Token


class AbstractTokenService(ABC):
    """Port for issuing and verifying access tokens."""

    @abstractmethod
    def encode(self, username: str, roles: Collection[Role]) -> str: ...

    @abstractmethod
    def decode(self, encoded_token: str) -> Token:
        """Return the claims of ``encoded_token``, or raise InvalidTokenError."""
