from email.message import EmailMessage

from email_detection_layer.config import EmailSettings
from email_detection_layer.models import DetectedEmail
from email_detection_layer.pipeline import EmailIngestionPipeline
from email_detection_layer.state import EmailProcessingStatus, EmailStateStore
from email_detection_layer.storage import EmailArtifactStore
from job_queue.models import JobStatus
from job_queue.repository import SQLiteJobQueue


class FakeImap:
    def __init__(self, messages):
        self.messages = messages
        self.logged_out = False

    def uid(self, command, value, query):
        if command == "search":
            return "OK", [b" ".join(str(uid).encode() for uid in self.messages)]
        return "OK", [(b"header", self.messages[int(value)])]

    def logout(self):
        self.logged_out = True


def settings(tmp_path):
    return EmailSettings(
        imap_host="imap.example.com",
        imap_username="quotes@example.com",
        imap_password="secret",
        state_db_path=str(tmp_path / "state.db"),
        data_dir=str(tmp_path / "data"),
    )


def raw_email(subject: str) -> bytes:
    message = EmailMessage()
    message["Message-ID"] = f"<{subject.lower()}@example.com>"
    message["From"] = "customer@example.com"
    message["To"] = "quotes@example.com"
    message["Subject"] = subject
    message.set_content("Please send a quotation.")
    return message.as_bytes()


def test_pipeline_retrieves_persists_and_enqueues(tmp_path):
    config = settings(tmp_path)
    state = EmailStateStore(config.state_db_path)
    queue = SQLiteJobQueue(config.state_db_path)
    imap = FakeImap({4: raw_email("Quote Request")})
    pipeline = EmailIngestionPipeline(
        config,
        state,
        queue,
        EmailArtifactStore(config.data_dir),
        connection_factory=lambda _: (True, imap),
    )

    assert pipeline.run() == 1
    job = queue.claim_next("agent-worker")
    assert job is not None
    assert job.job.status is JobStatus.RUNNING
    assert state.get_last_queued_uid("INBOX") == 4
    assert state.get_record(DetectedEmail(uid=4, mailbox="INBOX")).status is EmailProcessingStatus.QUEUED
    assert imap.logged_out is True
    assert list((tmp_path / "data" / "emails" / "raw").glob("*.eml"))
    assert list((tmp_path / "data" / "emails" / "normalized").glob("*.json"))
    queue.close()
    state.close()


def test_pipeline_continues_after_a_message_failure(tmp_path):
    config = settings(tmp_path)
    state = EmailStateStore(config.state_db_path)
    queue = SQLiteJobQueue(config.state_db_path)
    imap = FakeImap({4: b"", 5: raw_email("Valid Request")})
    pipeline = EmailIngestionPipeline(
        config,
        state,
        queue,
        EmailArtifactStore(config.data_dir),
        connection_factory=lambda _: (True, imap),
    )

    assert pipeline.run() == 1
    failed = state.get_record(DetectedEmail(uid=4, mailbox="INBOX"))
    queued = state.get_record(DetectedEmail(uid=5, mailbox="INBOX"))
    assert failed.status is EmailProcessingStatus.FAILED
    assert queued.status is EmailProcessingStatus.QUEUED
    assert queue.claim_next("agent-worker") is not None
    queue.close()
    state.close()
