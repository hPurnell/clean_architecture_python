from typing import Any

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler
from litestar.types import Guard

from app.auth.domain.role import Role


def requires_role(*roles: Role) -> Guard:
    """Refuse the request unless the token carries one of ``roles``.

    Authorization, not authentication: the middleware has already decided who
    the caller is by the time a guard runs, and a caller who is nobody never
    gets this far.
    """

    def guard(
        connection: ASGIConnection[Any, Any, Any, Any], _: BaseRouteHandler
    ) -> None:
        held: list[str] = getattr(connection.user, "roles", [])
        if not any(role.value in held for role in roles):
            raise PermissionDeniedException(
                "This action needs one of: " + ", ".join(role.value for role in roles)
            )

    return guard
