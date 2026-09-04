from typing import Any

from dishka import Provider, make_async_container
from dishka.integrations import faststream as faststream_integration
from dishka.integrations import litestar as litestar_integration
from litestar import Litestar
from litestar.middleware.base import DefineMiddleware
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, Reference, SecurityScheme

from app.auth.controllers.auth_ctrl import AuthController
from app.auth.controllers.authentication_middleware import (
    JWTAuthenticationMiddleware,
)
from app.auth.service.jwt_token_service import JwtTokenService
from app.broker import Broker
from app.config import config
from app.dishka_dependencies import (
    AppProvider,
    IntegrationTestProvider,
    UnitTestProvider,
)
from app.faststream_app_factory import create_faststream_app, lifespan_broker
from app.items.controllers import ItemController, ItemsCommandsDecoupledCtrl
from app.jobs.controllers import JobController
from app.shared.web.exception_handlers import EXCEPTION_HANDLERS


# The factories differ only in which components the container is assembled
# from; how the app behaves at the edge is _build_app's, and no caller's.
def create_app() -> Litestar:
    return _build_app(AppProvider())


def create_unit_test_app() -> Litestar:
    return _build_app(UnitTestProvider())


def create_integration_test_app() -> Litestar:
    return _build_app(IntegrationTestProvider())


def _build_app(provider: Provider) -> Litestar:
    app = Litestar(
        # Never hardcoded: debug serves tracebacks and internals to the caller.
        debug=config.DEBUG,
        route_handlers=get_route_handlers(),
        openapi_config=create_openapi_config(),
        exception_handlers=EXCEPTION_HANDLERS,
        # Built here, not passed in: authentication a caller can leave out is
        # eventually left out, and the tests build their own apps. Routes opt
        # out individually with `exclude_from_auth`.
        middleware=[create_auth_middleware()],
        on_startup=[on_startup],
        on_shutdown=[on_shutdown],
        lifespan=[lifespan_broker],
    )
    faststream_app = create_faststream_app()
    broker = faststream_app.broker
    container = make_async_container(provider, context={Broker: broker})
    app.state.broker = broker
    litestar_integration.setup_dishka(container, app)
    faststream_integration.setup_dishka(container, faststream_app, auto_inject=True)
    return app


def get_route_handlers() -> list[Any]:
    return [AuthController, ItemController, ItemsCommandsDecoupledCtrl, JobController]


def create_openapi_config() -> OpenAPIConfig:
    security_schemes: dict[str, SecurityScheme | Reference] = {
        "BearerAuth": SecurityScheme(
            type="http",
            scheme="bearer",
            bearer_format="JWT",
        )
    }
    openapi_config = OpenAPIConfig(
        title="My API",
        version="1.0.0",
        description="A sample Litestar API with Swagger enabled",
        components=Components(security_schemes=security_schemes),
        security=[{"BearerAuth": []}],
    )
    return openapi_config


def create_auth_middleware() -> DefineMiddleware:
    # Built by Litestar, not the container, so the token service is explicit.
    return DefineMiddleware(
        JWTAuthenticationMiddleware,
        # Anchored: `exclude` is matched with findall, so a bare "schema"
        # would skip authentication on any path merely containing it.
        exclude="^/schema",
        token_service=JwtTokenService(secret=config.JWT_SECRET),
    )


async def on_startup(app: Litestar) -> None:
    return


async def on_shutdown(app: Litestar) -> None:
    return
