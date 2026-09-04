from typing import Any

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.types import ASGIApp

from app.auth.domain.abstract_token_service import AbstractTokenService
from app.auth.domain.errors import InvalidTokenError
from app.auth.domain.token import Token

API_KEY_HEADER = "Authorization"
BEARER_PREFIX = "Bearer"


class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    def __init__(
        self, app: ASGIApp, token_service: AbstractTokenService, **kwargs: Any
    ) -> None:
        super().__init__(app, **kwargs)
        self._token_service = token_service

    async def authenticate_request(
        self, connection: ASGIConnection[Any, Any, Any, Any]
    ) -> AuthenticationResult:
        auth_header = connection.headers.get(API_KEY_HEADER)
        if not auth_header:
            raise NotAuthorizedException()

        auth_header_split = auth_header.split(" ")
        if len(auth_header_split) != 2:
            raise NotAuthorizedException()

        if auth_header_split[0] != BEARER_PREFIX:
            raise NotAuthorizedException()

        bearer_token = auth_header_split[1]

        try:
            token: Token = self._token_service.decode(bearer_token)
        except InvalidTokenError as e:
            raise NotAuthorizedException(str(e)) from e

        return AuthenticationResult(user=token, auth=token)
