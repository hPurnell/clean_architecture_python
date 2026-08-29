from collections.abc import Iterator
from datetime import datetime
from typing import Any

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from app.auth.db.fake_user_respository import DEFAULT_PASSWORD, FakeUserRepository
from app.litestar_app_factory import create_integration_test_app, create_unit_test_app


@pytest.fixture(scope="function")
def fixture_unit_test_client() -> Iterator[TestClient[Litestar]]:
    app = create_unit_test_app()
    with TestClient(app=app) as client:
        yield client


@pytest.fixture(scope="function")
def fixture_unit_test_client_with_auth(
    fixture_valid_credentials: dict[str, Any],
) -> Iterator[TestClient[Litestar]]:
    app = create_unit_test_app()
    with TestClient(app=app) as client:
        auth_response = client.post("/auth/login", json=fixture_valid_credentials)
        auth_response_json = auth_response.json()
        client.headers["Authorization"] = f"Bearer {auth_response_json['access_token']}"
        yield client


@pytest.fixture(scope="function")
def fixture_integration_test_client() -> Iterator[TestClient[Litestar]]:
    app = create_integration_test_app()
    with TestClient(app=app) as client:
        yield client


@pytest.fixture(scope="function")
def fixture_integration_test_client_with_auth(
    fixture_valid_credentials: dict[str, Any],
) -> Iterator[TestClient[Litestar]]:
    app = create_integration_test_app()
    with TestClient(app=app) as client:
        auth_response = client.post("/auth/login", json=fixture_valid_credentials)
        auth_response_json = auth_response.json()
        client.headers["Authorization"] = f"Bearer {auth_response_json['access_token']}"
        yield client


@pytest.fixture(scope="function")
def fixture_valid_credentials():
    # The stored user only has the hash, so the password comes from the
    # constant the fake repository seeded itself from.
    mock_user_repository: FakeUserRepository = FakeUserRepository()
    user = mock_user_repository.get_user("john.doe@example.com")
    assert user is not None
    return {"username": user.username, "password": DEFAULT_PASSWORD}


@pytest.fixture(scope="function")
def fixture_invalid_credentials():
    return {"username": "invalid.user@example.com", "password": "wrongpassword"}


@pytest.fixture
def fixture_new_item() -> dict[str, Any]:
    # Create a NewItem instance and return as a dictionary with PascalCase fields
    item = {"ValueStr": "Example String", "ValueInt": 42, "ValueFloat": 123.45}
    return item  # Return the dictionary directly


@pytest.fixture
def fixture_update_item() -> dict[str, Any]:
    # Create an UpdateItem instance and return as a dictionary with
    # PascalCase fields and date strings
    item = {
        "Id": None,  # Will be filled in by the test
        "ValueStr": "Updated String",
        "ValueInt": 99,
        "ValueFloat": 543.21,
        "CreatedDate": datetime(2024, 12, 31, 13, 17, 29).isoformat(),
        "ModifiedDate": datetime(2024, 12, 31, 13, 45, 10).isoformat(),
    }
    return item  # Return the dictionary directly
