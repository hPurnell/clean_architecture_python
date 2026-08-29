from abc import ABC, abstractmethod

from app.auth.domain.token import Token


class AbstractAuthService(ABC):
    """
    Port for exchanging credentials for a token, and a token for its claims.
    """

    @abstractmethod
    def login(self, username: str, password: str) -> str:
        """Return an encoded token for ``username``.

        Raises:
            InvalidCredentialsError: if the user is unknown or the password
                does not match. The two are not distinguished: telling them
                apart tells a caller which usernames exist.
        """

    @abstractmethod
    def verify(self, encoded_token: str) -> Token:
        """Return the claims carried by ``encoded_token``.

        Raises:
            InvalidTokenError: if the token is malformed, expired, or unsigned
                by this service.
        """
