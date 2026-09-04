from typing import Any

import pytest
from litestar import Litestar
from litestar.testing import TestClient


# These share RabbitMQ queues, so they must not run concurrently under
# `pytest -n auto`. xdist_group keeps them on one worker, given --dist loadgroup.
@pytest.mark.xdist_group("item_integration")
@pytest.mark.integration
class TestItemCtrlIntegration:

    def test_post_items_get_items(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        client = fixture_integration_test_client_with_auth

        # POST item 1, passing the dictionary directly as the request body
        response = client.post("/items", json=fixture_new_item)
        assert response.is_success

        response = client.get("/items")
        response_json = response.json()
        assert response.is_success
        assert len(response_json) == 1  # Adjusted to match one item for this test case
        assert response_json[0]["Id"] is not None

    def test_post_item_get_item(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        response = fixture_integration_test_client_with_auth.post(
            "/items",
            json=fixture_new_item,  # Pass the dictionary directly
        )
        assert response.is_success

        response = fixture_integration_test_client_with_auth.get("/items")
        assert response.is_success
        items = response.json()
        assert len(items) == 1

        item_id = items[0]["Id"]
        response = fixture_integration_test_client_with_auth.get(f"/items/{item_id}")
        assert response.is_success
        item = response.json()
        assert item["Id"] == item_id
        assert item["ValueStr"] == fixture_new_item["ValueStr"]
        assert item["ValueInt"] == fixture_new_item["ValueInt"]
        assert item["ValueFloat"] == fixture_new_item["ValueFloat"]

    def test_delete_item(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        response = fixture_integration_test_client_with_auth.post(
            "/items",
            json=fixture_new_item,  # Pass the dictionary directly
        )
        assert response.is_success

        response = fixture_integration_test_client_with_auth.get("/items")
        assert response.is_success
        item_id = response.json()[0]["Id"]

        response = fixture_integration_test_client_with_auth.delete(f"/items/{item_id}")
        assert response.is_success

        response = fixture_integration_test_client_with_auth.get("/items")
        assert response.is_success
        assert len(response.json()) == 0

    def test_get_item_not_found(
        self, fixture_integration_test_client_with_auth: TestClient[Litestar]
    ):
        response = fixture_integration_test_client_with_auth.get("/items/999999")
        assert response.status_code == 404

    def test_patch_item(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
        fixture_update_item: dict[str, Any],
    ):
        response = fixture_integration_test_client_with_auth.post(
            "/items",
            json=fixture_new_item,  # Pass the dictionary directly
        )
        assert response.is_success

        response = fixture_integration_test_client_with_auth.get("/items")
        assert response.is_success
        item_id = response.json()[0]["Id"]

        update_item = fixture_update_item
        update_item["Id"] = item_id  # Modify the update item to include the ID
        response = fixture_integration_test_client_with_auth.patch(
            "/items",
            json=update_item,  # Send the updated item as JSON
        )
        assert response.is_success

        response = fixture_integration_test_client_with_auth.get("/items")
        item = response.json()[0]

        assert item["Id"] == item_id
        assert item["ValueStr"] == update_item["ValueStr"]
        assert item["ValueInt"] == update_item["ValueInt"]
        assert item["ValueFloat"] == update_item["ValueFloat"]

    def test_patch_item_leaves_out_what_it_does_not_name(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        """A PATCH carrying two fields must not blank the third.

        Every other patch test here sends a whole item, which is what hid this.
        """
        client = fixture_integration_test_client_with_auth

        response = client.post("/items", json=fixture_new_item)
        assert response.is_success
        item_id = response.json()["Id"]

        response = client.patch("/items", json={"Id": item_id, "ValueStr": "changed"})
        assert response.is_success

        item = client.get(f"/items/{item_id}").json()
        assert item["ValueStr"] == "changed"
        assert item["ValueInt"] == fixture_new_item["ValueInt"]
        assert item["ValueFloat"] == fixture_new_item["ValueFloat"]
