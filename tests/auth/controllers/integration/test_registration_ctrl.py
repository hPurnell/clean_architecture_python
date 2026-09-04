from typing import Any

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from app.auth.db.fake_user_repository import DEFAULT_PASSWORD, DEFAULT_USERNAME

NEW_USER = {
    "name": "Ada Lovelace",
    "username": "ada@example.com",
    "password": "a long enough password",
}


@pytest.mark.integration
class TestRegistration:
    def test_register_then_log_in(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        client = fixture_integration_test_client

        response = client.post("/auth/register", json=NEW_USER)
        assert response.status_code == 201
        assert response.json()["username"] == NEW_USER["username"]

        response = client.post(
            "/auth/login",
            json={"username": NEW_USER["username"], "password": NEW_USER["password"]},
        )
        assert response.is_success
        assert response.json()["access_token"]

    def test_registering_does_not_echo_the_password(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        response = fixture_integration_test_client.post("/auth/register", json=NEW_USER)

        assert NEW_USER["password"] not in response.text

    def test_a_taken_username_is_a_conflict(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        client = fixture_integration_test_client
        client.post("/auth/register", json=NEW_USER)

        assert client.post("/auth/register", json=NEW_USER).status_code == 409

    def test_a_weak_password_is_refused(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        response = fixture_integration_test_client.post(
            "/auth/register", json={**NEW_USER, "password": "short"}
        )

        assert response.status_code == 400


@pytest.mark.integration
class TestChangePassword:
    def test_changing_a_password_needs_a_token(
        self, fixture_integration_test_client: TestClient[Litestar]
    ):
        # The controller is no longer excluded from auth as a whole.
        response = fixture_integration_test_client.post(
            "/auth/password",
            json={"current_password": DEFAULT_PASSWORD, "new_password": "x" * 12},
        )

        assert response.status_code == 401

    def test_the_new_password_is_the_one_that_works(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_valid_credentials: dict[str, Any],
    ):
        client = fixture_integration_test_client_with_auth
        new_password = "a brand new password"

        response = client.post(
            "/auth/password",
            json={
                "current_password": DEFAULT_PASSWORD,
                "new_password": new_password,
            },
        )
        assert response.status_code == 204

        assert client.post(
            "/auth/login",
            json={"username": DEFAULT_USERNAME, "password": new_password},
        ).is_success
        assert (
            client.post("/auth/login", json=fixture_valid_credentials).status_code
            == 401
        )

    def test_the_token_says_whose_password_changes(
        self, fixture_integration_test_client_with_auth: TestClient[Litestar]
    ):
        # There is no username in the body: a caller cannot aim this at
        # somebody else's account.
        client = fixture_integration_test_client_with_auth

        response = client.post(
            "/auth/password",
            json={
                "current_password": "not the password",
                "new_password": "a brand new password",
            },
        )

        assert response.status_code == 401
