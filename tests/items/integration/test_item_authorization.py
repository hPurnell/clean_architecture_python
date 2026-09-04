from typing import Any

import pytest
from litestar import Litestar
from litestar.testing import TestClient


@pytest.mark.xdist_group("item_integration")
@pytest.mark.integration
class TestDeletingNeedsAdmin:
    """Roles gate destruction; everything else is open to any signed-in user.

    A placeholder policy, but roles have to gate something to be worth having.
    """

    def test_a_plain_user_may_create_and_read(
        self,
        fixture_integration_test_client_without_admin: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        client = fixture_integration_test_client_without_admin

        assert client.post("/items", json=fixture_new_item).is_success
        assert client.get("/items").is_success

    def test_a_plain_user_may_not_delete(
        self,
        fixture_integration_test_client_without_admin: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        client = fixture_integration_test_client_without_admin
        item_id = client.post("/items", json=fixture_new_item).json()["Id"]

        assert client.delete(f"/items/{item_id}").status_code == 403

    def test_an_admin_may_delete(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        client = fixture_integration_test_client_with_auth
        item_id = client.post("/items", json=fixture_new_item).json()["Id"]

        assert client.delete(f"/items/{item_id}").is_success

    def test_the_decoupled_route_is_guarded_too(
        self,
        fixture_integration_test_client_without_admin: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        # Publishing the command is still doing it, so the same rule applies.
        client = fixture_integration_test_client_without_admin
        item_id = client.post("/items", json=fixture_new_item).json()["Id"]

        assert client.delete(f"/items_decoupled/{item_id}").status_code == 403

    def test_an_anonymous_caller_is_unauthorised_not_forbidden(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        # 401 before 403: the guard never runs for a caller who is nobody.
        assert fixture_integration_test_client.delete("/items/1").status_code == 401
