import time
from typing import Any

import pytest
from litestar import Litestar
from litestar.testing import TestClient

# The subscriber runs in its own task, so the job is the only thing to wait on.
JOB_TIMEOUT_SECONDS = 10.0
JOB_POLL_SECONDS = 0.05


def wait_for_job(client: TestClient[Litestar], job_id: str) -> dict[str, Any]:
    """Poll a job until it reports an outcome, and return it."""
    deadline = time.monotonic() + JOB_TIMEOUT_SECONDS
    while True:
        response = client.get(f"/jobs/{job_id}")
        assert response.is_success
        job: dict[str, Any] = response.json()
        if job["Status"] in ("SUCCEEDED", "FAILED"):
            return job
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"Job {job_id} was still {job['Status']} after "
                f"{JOB_TIMEOUT_SECONDS}s"
            )
        time.sleep(JOB_POLL_SECONDS)


def dispatch(client: TestClient[Litestar], method: str, path: str, **kwargs) -> str:
    """Send a decoupled command and return the id of the job it was given."""
    response = client.request(method, path, **kwargs)
    assert response.status_code == 202
    job = response.json()
    assert job["Id"]
    assert job["Status"] == "PENDING"
    return str(job["Id"])


# Shares TestItemCtrlIntegration's queues, so it shares its xdist group.
@pytest.mark.xdist_group("item_integration")
@pytest.mark.integration
class TestItemDecoupledCtrlIntegration:

    def test_post_item(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        client = fixture_integration_test_client_with_auth

        job_id = dispatch(client, "POST", "/items_decoupled", json=fixture_new_item)

        job = wait_for_job(client, job_id)
        assert job["Status"] == "SUCCEEDED"
        assert job["Command"] == "create_item"
        assert job["Error"] is None

        # The job's result is the id of the item the command created.
        response = client.get(f"/items/{job['Result']}")
        assert response.is_success
        assert response.json()["ValueStr"] == fixture_new_item["ValueStr"]

    def test_delete_item(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
    ):
        client = fixture_integration_test_client_with_auth

        job_id = dispatch(client, "POST", "/items_decoupled", json=fixture_new_item)
        item_id = wait_for_job(client, job_id)["Result"]

        job_id = dispatch(client, "DELETE", f"/items_decoupled/{item_id}")

        assert wait_for_job(client, job_id)["Status"] == "SUCCEEDED"
        response = client.get("/items")
        assert response.is_success
        assert len(response.json()) == 0

    def test_patch_item(
        self,
        fixture_integration_test_client_with_auth: TestClient[Litestar],
        fixture_new_item: dict[str, Any],
        fixture_update_item: dict[str, Any],
    ):
        client = fixture_integration_test_client_with_auth

        job_id = dispatch(client, "POST", "/items_decoupled", json=fixture_new_item)
        item_id = wait_for_job(client, job_id)["Result"]

        update_item = fixture_update_item
        update_item["Id"] = int(item_id)
        job_id = dispatch(client, "PATCH", "/items_decoupled", json=update_item)

        assert wait_for_job(client, job_id)["Status"] == "SUCCEEDED"
        response = client.get(f"/items/{item_id}")
        assert response.is_success
        item = response.json()
        assert item["ValueStr"] == update_item["ValueStr"]
        assert item["ValueInt"] == update_item["ValueInt"]
        assert item["ValueFloat"] == update_item["ValueFloat"]

    def test_a_command_that_cannot_be_carried_out_fails_its_job(
        self, fixture_integration_test_client_with_auth: TestClient[Litestar]
    ):
        # Accepted: nothing has looked for the item yet. The job reports it.
        client = fixture_integration_test_client_with_auth

        job_id = dispatch(client, "DELETE", "/items_decoupled/999999")

        job = wait_for_job(client, job_id)
        assert job["Status"] == "FAILED"
        assert "999999" in job["Error"]

    def test_get_unknown_job(
        self, fixture_integration_test_client_with_auth: TestClient[Litestar]
    ):
        response = fixture_integration_test_client_with_auth.get("/jobs/no-such-job")
        assert response.status_code == 404
