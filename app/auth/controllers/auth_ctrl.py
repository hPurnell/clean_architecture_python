from typing import Any

from dishka.integrations.litestar import FromDishka, inject
from litestar import Controller, Request, Response, post
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth.controllers.auth_dto import (
    AuthRequest,
    AuthResponse,
    ChangePasswordRequest,
    RegisteredResponse,
    RegisterRequest,
)
from app.auth.domain.abstract_auth_service import AbstractAuthService
from app.auth.domain.token import Token


class AuthController(Controller):
    tags = ["Auth"]

    # Not excluded as a whole: /auth/password is the one route here that has to
    # know who is asking.
    @post(path="/auth/register", exclude_from_auth=True, status_code=HTTP_201_CREATED)
    @inject
    async def register(
        self, data: RegisterRequest, auth_service: FromDishka[AbstractAuthService]
    ) -> Response[Any]:
        user = auth_service.register(data.name, data.username, data.password)
        return Response(
            content=RegisteredResponse(
                id=user.id, name=user.name, username=user.username
            ).model_dump(),
            status_code=HTTP_201_CREATED,
            media_type="application/json",
        )

    @post(path="/auth/login", exclude_from_auth=True)
    @inject
    async def login(
        self, data: AuthRequest, auth_service: FromDishka[AbstractAuthService]
    ) -> Response[Any]:
        token = auth_service.login(data.username, data.password)
        return Response(
            content=AuthResponse(access_token=token).model_dump(),
            media_type="application/json",
        )

    @post(path="/auth/password", status_code=HTTP_204_NO_CONTENT)
    @inject
    async def change_password(
        self,
        data: ChangePasswordRequest,
        request: Request[Token, Token, Any],
        auth_service: FromDishka[AbstractAuthService],
    ) -> None:
        # Whose password changes is the token's to say, never the body's.
        auth_service.change_password(
            request.user.sub, data.current_password, data.new_password
        )
