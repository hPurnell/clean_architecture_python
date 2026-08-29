from typing import Any

import pytest
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AuthenticationResult

from app.auth.service.jwt_token_service import JwtTokenService
from app.authentication_middleware import JWTAuthenticationMiddleware

JWT_SECRET = "supersecretkey"


async def _noop_asgi(scope: Any, receive: Any, send: Any) -> None:
    # The next app in the stack; authenticate_request never calls it.
    return None


class _FakeConnection:
    """The slice of ASGIConnection that authenticate_request actually touches."""

    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


@pytest.fixture
def token_service() -> JwtTokenService:
    return JwtTokenService(secret=JWT_SECRET)


@pytest.fixture
def middleware(token_service: JwtTokenService) -> JWTAuthenticationMiddleware:
    return JWTAuthenticationMiddleware(app=_noop_asgi, token_service=token_service)


@pytest.mark.unit
@pytest.mark.asyncio
class TestJWTAuthenticationMiddleware:
    async def test_a_valid_bearer_token_authenticates_the_request(
        self, middleware: JWTAuthenticationMiddleware, token_service: JwtTokenService
    ):
        token = token_service.encode("john.doe@example.com")

        result = await middleware.authenticate_request(
            _FakeConnection({"Authorization": f"Bearer {token}"})  # type: ignore[arg-type]
        )

        assert isinstance(result, AuthenticationResult)
        # Both the identity and the raw auth are the decoded claims.
        assert result.user.sub == "john.doe@example.com"
        assert result.auth.sub == "john.doe@example.com"

    async def test_a_missing_authorization_header_is_rejected(
        self, middleware: JWTAuthenticationMiddleware
    ):
        with pytest.raises(NotAuthorizedException):
            await middleware.authenticate_request(_FakeConnection({}))  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "header_value",
        [
            "",
            "Bearer",  # scheme only, no token
            "Bearer a b",  # three parts
            "Bearer  token",  # the extra space makes an empty middle part
            "Token abc",  # unknown scheme
            "Basic dXNlcjpwYXNz",  # a different scheme
            "bearer abc",  # scheme match is case-sensitive
        ],
    )
    async def test_a_malformed_authorization_header_is_rejected(
        self, middleware: JWTAuthenticationMiddleware, header_value: str
    ):
        with pytest.raises(NotAuthorizedException):
            await middleware.authenticate_request(
                _FakeConnection({"Authorization": header_value})  # type: ignore[arg-type]
            )

    async def test_a_bearer_token_that_is_not_a_jwt_is_rejected(
        self, middleware: JWTAuthenticationMiddleware
    ):
        with pytest.raises(NotAuthorizedException):
            await middleware.authenticate_request(
                _FakeConnection({"Authorization": "Bearer not.a.jwt"})  # type: ignore[arg-type]
            )

    async def test_a_token_signed_with_another_secret_is_rejected(
        self, middleware: JWTAuthenticationMiddleware
    ):
        foreign = JwtTokenService(secret="a-different-secret").encode("john")

        with pytest.raises(NotAuthorizedException):
            await middleware.authenticate_request(
                _FakeConnection({"Authorization": f"Bearer {foreign}"})  # type: ignore[arg-type]
            )

    async def test_the_token_error_message_reaches_the_response(
        self, middleware: JWTAuthenticationMiddleware
    ):
        # A bad token carries the domain error's text; a malformed header does
        # not, so the two failures stay distinguishable in logs.
        with pytest.raises(NotAuthorizedException, match="Invalid token"):
            await middleware.authenticate_request(
                _FakeConnection({"Authorization": "Bearer not.a.jwt"})  # type: ignore[arg-type]
            )
