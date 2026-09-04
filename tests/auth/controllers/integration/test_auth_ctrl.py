from typing import Any

import pytest
from litestar import Litestar
from litestar.status_codes import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from litestar.testing import TestClient

from app.auth.domain.role import Role
from app.auth.service.jwt_token_service import JwtTokenService


@pytest.mark.integration
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
        assert response.status_code == HTTP_401_UNAUTHORIZED

    def test_login_response_carries_a_bearer_token(
        self,
        fixture_integration_test_client: TestClient[Litestar],
        fixture_valid_credentials: dict[str, Any],
    ):
        response = fixture_integration_test_client.post(
            "/auth/login", json=fixture_valid_credentials
        )

        assert response.status_code == HTTP_201_CREATED
        body = response.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"

    def test_login_is_case_insensitive_in_the_username(
        self,
        fixture_integration_test_client: TestClient[Litestar],
        fixture_valid_credentials: dict[str, Any],
    ):
        shouting = {
            **fixture_valid_credentials,
            "username": fixture_valid_credentials["username"].upper(),
        }

        response = fixture_integration_test_client.post("/auth/login", json=shouting)

        assert response.status_code == HTTP_201_CREATED
        assert response.json()["access_token"]

    def test_login_with_a_malformed_body_is_a_400(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        response = fixture_integration_test_client.post("/auth/login", json={})

        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_wrong_password_and_unknown_user_return_the_same_401(
        self,
        fixture_integration_test_client: TestClient[Litestar],
        fixture_valid_credentials: dict[str, Any],
        fixture_invalid_credentials: dict[str, Any],
    ):
        wrong_password = fixture_integration_test_client.post(
            "/auth/login",
            json={**fixture_valid_credentials, "password": "not the password"},
        )
        unknown_user = fixture_integration_test_client.post(
            "/auth/login", json=fixture_invalid_credentials
        )

        assert wrong_password.status_code == HTTP_401_UNAUTHORIZED
        assert unknown_user.status_code == HTTP_401_UNAUTHORIZED
        # Identical body: the response must not reveal which usernames exist.
        assert wrong_password.json() == unknown_user.json()
        assert "access_token" not in wrong_password.json()

    @pytest.mark.parametrize(
        "authorization",
        [
            "Bearer not.a.jwt",
            "Bearer",
            "Basic dXNlcjpwYXNz",
            "bearer sometoken",
        ],
    )
    def test_a_bad_authorization_header_is_rejected_at_a_secured_route(
        self,
        fixture_integration_test_client: TestClient[Litestar],
        authorization: str,
    ):
        response = fixture_integration_test_client.get(
            "/items", headers={"Authorization": authorization}
        )

        assert response.status_code == HTTP_401_UNAUTHORIZED

    def test_a_token_from_another_secret_is_rejected_at_a_secured_route(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        foreign = JwtTokenService(secret="a-different-secret").encode(
            "john.doe@example.com", {Role.USER}
        )

        response = fixture_integration_test_client.get(
            "/items", headers={"Authorization": f"Bearer {foreign}"}
        )

        assert response.status_code == HTTP_401_UNAUTHORIZED
