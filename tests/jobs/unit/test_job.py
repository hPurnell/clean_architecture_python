from datetime import datetime

import pytest

from app.jobs.domain.errors import InvalidJobTransitionError
from app.jobs.domain.job import ALLOWED_TRANSITIONS, Job, JobStatus

AT = datetime(2025, 1, 1, 12, 0, 0)
LATER = datetime(2025, 1, 1, 12, 0, 1)


def job_in(status: JobStatus) -> Job:
    return Job(id="j1", command="create_item", status=status, modified_date=AT)


@pytest.mark.unit
class TestJobLifecycle:
    def test_a_new_job_is_pending(self):
        assert Job(id="j1", command="create_item").status is JobStatus.PENDING

    def test_a_pending_job_starts(self):
        job = job_in(JobStatus.PENDING)

        job.start(AT)

        assert job.status is JobStatus.RUNNING

    def test_a_running_job_succeeds(self):
        job = job_in(JobStatus.RUNNING)

        job.succeed(LATER)

        assert job.status is JobStatus.SUCCEEDED

    def test_failing_records_why(self):
        job = job_in(JobStatus.RUNNING)

        job.fail("the connection dropped", AT)

        assert job.status is JobStatus.FAILED
        assert job.error == "the connection dropped"

    def test_every_move_stamps_the_modification_time(self):
        # A client polling the job has nothing else to tell it that it moved.
        job = job_in(JobStatus.PENDING)

        job.start(LATER)

        assert job.modified_date == LATER


@pytest.mark.unit
class TestIllegalTransitions:
    def test_a_job_cannot_succeed_without_having_run(self):
        with pytest.raises(InvalidJobTransitionError):
            job_in(JobStatus.PENDING).succeed(AT)

    @pytest.mark.parametrize("move", ["start", "succeed", "fail"])
    def test_nothing_follows_a_job_that_succeeded(self, move):
        """SUCCEEDED is terminal: a late redelivery must not rewrite it."""
        job = job_in(JobStatus.SUCCEEDED)
        arguments = ("late", AT) if move == "fail" else (AT,)

        with pytest.raises(InvalidJobTransitionError):
            getattr(job, move)(*arguments)

    def test_the_rejected_move_is_named_in_the_error(self):
        with pytest.raises(InvalidJobTransitionError) as raised:
            job_in(JobStatus.SUCCEEDED).start(AT)

        assert raised.value.current is JobStatus.SUCCEEDED
        assert raised.value.requested is JobStatus.RUNNING
        assert "SUCCEEDED" in str(raised.value)

    def test_a_rejected_move_leaves_the_job_alone(self):
        job = job_in(JobStatus.SUCCEEDED)

        with pytest.raises(InvalidJobTransitionError):
            job.fail("late", LATER)

        assert job.status is JobStatus.SUCCEEDED
        assert job.error is None
        assert job.modified_date == AT


@pytest.mark.unit
class TestRedelivery:
    """The broker decides what is retried, so the job has to allow for it."""

    def test_a_failed_job_can_be_run_again(self):
        # An unexpected error is recorded and re-raised for redelivery, so the
        # job that comes back is FAILED and must be able to start over.
        job = job_in(JobStatus.FAILED)

        job.start(LATER)

        assert job.status is JobStatus.RUNNING

    def test_a_job_still_running_can_be_run_again(self):
        # The consumer holding it died mid-command and the message came back.
        job = job_in(JobStatus.RUNNING)

        job.start(LATER)

        assert job.status is JobStatus.RUNNING

    def test_a_job_never_goes_back_to_pending(self):
        assert all(
            JobStatus.PENDING not in reachable
            for reachable in ALLOWED_TRANSITIONS.values()
        )

    def test_every_status_says_where_it_can_go(self):
        assert set(ALLOWED_TRANSITIONS) == set(JobStatus)
