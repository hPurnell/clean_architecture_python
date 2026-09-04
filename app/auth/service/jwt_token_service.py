from collections.abc import Collection
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import jwt

from app.auth.domain.abstract_token_service import AbstractTokenService
from app.auth.domain.errors import InvalidTokenError
from app.auth.domain.role import Role
from app.auth.domain.token import Token

DEFAULT_AUTH_DURATION = timedelta(hours=1)
DEFAULT_ALGORITHM = "HS256"


class JwtTokenService(AbstractTokenService):
    def __init__(
        self,
        secret: str,
        algorithm: str = DEFAULT_ALGORITHM,
        auth_duration: timedelta = DEFAULT_AUTH_DURATION,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._auth_duration = auth_duration

    def encode(self, username: str, roles: Collection[Role]) -> str:
        now = datetime.now(timezone.utc)
        token = Token(
            exp=(now + self._auth_duration).timestamp(),
            iat=now.timestamp(),
            sub=username,
            roles=sorted(role.value for role in roles),
        )
        return jwt.encode(asdict(token), self._secret, algorithm=self._algorithm)

    def decode(self, encoded_token: str) -> Token:
        try:
            payload = jwt.decode(
                jwt=encoded_token, key=self._secret, algorithms=[self._algorithm]
            )
        except jwt.exceptions.InvalidTokenError as e:
            raise InvalidTokenError() from e
        try:
            return Token(**payload)
        except TypeError as e:
            # Correctly signed, but not the shape this service issues.
            raise InvalidTokenError() from e
