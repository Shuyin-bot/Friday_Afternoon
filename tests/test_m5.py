from datetime import datetime, timedelta, timezone

import pytest

from job_queue.dispatcher import JobDispatcher, UnknownJobTypeError
from job_queue.models import Job, JobStatus, JobType
from job_queue.repository import InvalidClaimError, SQLiteJobQueue
from job_queue.worker import QueueWorker


def make_job(uid: int = 1) -> Job:
    return Job(job_type=JobType.EMAIL_RECEIVED, email_uid=uid, mailbox="INBOX")


def test_enqueue_is_idempotent_per_email_and_job_type(tmp_path):
    queue = SQLiteJobQueue(str(tmp_path / "queue.db"))

    first = queue.enqueue(make_job())
    duplicate = queue.enqueue(make_job())

    assert duplicate.id == first.id
    assert queue.get(str(first.id)).status is JobStatus.PENDING
    queue.close()


def test_claim_and_complete_require_the_worker_lease(tmp_path):
    queue = SQLiteJobQueue(str(tmp_path / "queue.db"))
    job = queue.enqueue(make_job())

    claimed = queue.claim_next("worker-a")

    assert claimed is not None
    assert claimed.job.id == job.id
    assert claimed.job.status is JobStatus.RUNNING
    assert queue.claim_next("worker-b") is None
    with pytest.raises(InvalidClaimError):
        queue.complete(str(job.id), "worker-b")

    completed = queue.complete(str(job.id), "worker-a")
    assert completed.status is JobStatus.COMPLETED
    queue.close()


def test_expired_lease_can_be_reclaimed(tmp_path):
    queue = SQLiteJobQueue(str(tmp_path / "queue.db"))
    queue.enqueue(make_job())
    start = datetime.now(timezone.utc)
    first = queue.claim_next("worker-a", lease_seconds=10, now=start)
    second = queue.claim_next("worker-b", lease_seconds=10, now=start + timedelta(seconds=11))

    assert first is not None
    assert second is not None
    assert second.job.id == first.job.id
    assert second.job.attempts == 2
    queue.close()


def test_repeated_worker_crash_enters_dead_letter(tmp_path):
    queue = SQLiteJobQueue(str(tmp_path / "queue.db"), max_attempts=1)
    queue.enqueue(make_job())
    start = datetime.now(timezone.utc)

    assert queue.claim_next("worker-a", lease_seconds=1, now=start) is not None
    assert queue.claim_next("worker-b", now=start + timedelta(seconds=2)) is None
    assert queue.list_dead_letters()[0].status is JobStatus.DEAD_LETTER
    queue.close()


def test_failed_jobs_retry_then_enter_dead_letter(tmp_path):
    queue = SQLiteJobQueue(str(tmp_path / "queue.db"))
    job = queue.enqueue(make_job())
    start = datetime.now(timezone.utc)

    first_claim = queue.claim_next("worker-a", now=start)
    retrying = queue.fail(str(job.id), "worker-a", "temporary failure", max_attempts=2, now=start)
    assert first_claim is not None
    assert retrying.status is JobStatus.RETRYING
    assert queue.claim_next("worker-a", now=start + timedelta(milliseconds=500)) is None

    second_claim = queue.claim_next("worker-a", now=start + timedelta(seconds=1))
    dead = queue.fail(
        str(job.id),
        "worker-a",
        "permanent failure",
        max_attempts=2,
        now=start + timedelta(seconds=1),
    )

    assert second_claim is not None
    assert dead.status is JobStatus.DEAD_LETTER
    assert queue.list_dead_letters()[0].id == job.id
    queue.close()


def test_worker_dispatches_and_completes_job(tmp_path):
    queue = SQLiteJobQueue(str(tmp_path / "queue.db"))
    job = queue.enqueue(make_job())
    handled = []
    dispatcher = JobDispatcher({"EMAIL_RECEIVED": lambda received: handled.append(received.id)})
    worker = QueueWorker(queue, dispatcher, "worker-a")

    assert worker.run_once() is True
    assert handled == [job.id]
    assert queue.get(str(job.id)).status is JobStatus.COMPLETED
    assert worker.run_once() is False
    queue.close()


def test_dispatcher_rejects_unregistered_job_type():
    dispatcher = JobDispatcher()

    with pytest.raises(UnknownJobTypeError):
        dispatcher.dispatch(make_job())
