from typing import Any

from dishka.integrations.litestar import FromDishka, inject
from litestar import Controller, Response, post

from app.auth.controllers.auth_dto import AuthRequest, AuthResponse
from app.auth.service.auth_service import AuthService


class AuthController(Controller):
    tags = ["Auth"]
    exclude_from_auth = True

    @post(path="/auth/login", exclude_from_auth=True)
    @inject
    async def login(
        self, data: AuthRequest, auth_service: FromDishka[AuthService]
    ) -> Response[Any]:
        token = auth_service.login(data.username, data.password)
        return Response(
            content=AuthResponse(access_token=token).model_dump(),
            media_type="application/json",
        )
