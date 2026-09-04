import pytest
from litestar import Litestar
from litestar.middleware.base import DefineMiddleware

from app.authentication_middleware import JWTAuthenticationMiddleware
from app.config import config
from app.litestar_app_factory import (
    create_app,
    create_integration_test_app,
    create_unit_test_app,
)

# Every app this project can build, the deployed one first: the tests assemble
# their own, so asserting only on those says nothing about what serves traffic.
APP_FACTORIES = [create_app, create_unit_test_app, create_integration_test_app]


def authentication_middleware(app: Litestar) -> list[DefineMiddleware]:
    return [
        middleware
        for middleware in app.middleware
        if isinstance(middleware, DefineMiddleware)
        and middleware.middleware is JWTAuthenticationMiddleware
    ]


@pytest.mark.unit
@pytest.mark.parametrize("create", APP_FACTORIES, ids=lambda create: create.__name__)
class TestEveryApplication:
    def test_authenticates_its_requests(self, create):
        """No app may be assembled without the authentication middleware."""
        assert authentication_middleware(create())

    def test_takes_its_debug_setting_from_the_configuration(self, create, monkeypatch):
        # Hardcoding it on serves tracebacks and internal state to callers.
        monkeypatch.setattr(config, "DEBUG", False)
        assert create().debug is False

        monkeypatch.setattr(config, "DEBUG", True)
        assert create().debug is True
