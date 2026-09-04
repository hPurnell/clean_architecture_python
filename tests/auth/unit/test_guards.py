from typing import Any

import pytest
from litestar.exceptions import PermissionDeniedException

from app.auth.controllers.guards import requires_role
from app.auth.domain.role import Role
from app.auth.domain.token import Token


class _Connection:
    def __init__(self, user: Any) -> None:
        self.user = user


def connection_for(*roles: Role) -> Any:
    return _Connection(
        Token(exp=0.0, iat=0.0, sub="ada@example.com", roles=[r.value for r in roles])
    )


@pytest.mark.unit
class TestRequiresRole:
    def test_the_role_the_route_asks_for_is_allowed(self):
        requires_role(Role.ADMIN)(connection_for(Role.ADMIN), None)  # type: ignore[arg-type]

    def test_one_of_several_is_enough(self):
        guard = requires_role(Role.ADMIN, Role.USER)

        guard(connection_for(Role.USER), None)  # type: ignore[arg-type]

    def test_a_role_the_caller_does_not_hold_is_refused(self):
        with pytest.raises(PermissionDeniedException):
            requires_role(Role.ADMIN)(connection_for(Role.USER), None)  # type: ignore[arg-type]

    def test_no_roles_at_all_is_refused(self):
        with pytest.raises(PermissionDeniedException):
            requires_role(Role.ADMIN)(connection_for(), None)  # type: ignore[arg-type]

    def test_the_refusal_names_what_was_needed(self):
        with pytest.raises(PermissionDeniedException, match="admin"):
            requires_role(Role.ADMIN)(connection_for(Role.USER), None)  # type: ignore[arg-type]
