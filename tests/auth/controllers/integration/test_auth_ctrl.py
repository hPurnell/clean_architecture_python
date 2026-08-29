from typing import Any

from litestar import Litestar
from litestar.testing import TestClient


class TestSecuredEndpoint:
    def test_login_and_access_secured_endpoint(
        self,
        fixture_integration_test_client: TestClient[Litestar],
        fixture_valid_credentials: dict[str, Any],
    ):
        response = fixture_integration_test_client.post(
            "/auth/login", json=fixture_valid_credentials
        )
        assert response.is_success

        response_json = response.json()
        assert "access_token" in response_json
        token = response_json["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = fixture_integration_test_client.get("/items", headers=headers)

        assert response.is_success

    def test_failed_login(
        self,
        fixture_integration_test_client: TestClient[Litestar],
        fixture_invalid_credentials: dict[str, Any],
    ):
        response = fixture_integration_test_client.post(
            "/auth/login", json=fixture_invalid_credentials
        )
        assert not response.is_success

        response_json = response.json()
        assert "access_token" not in response_json

    def test_access_secured_endpoint_without_login(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        response = fixture_integration_test_client.get("/items")
        assert not response.is_success
