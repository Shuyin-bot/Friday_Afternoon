from pathlib import Path

import pytest
from pydantic import ValidationError

from email_detection_layer.config import EmailSettings
from email_detection_layer.models import DetectedEmail
from job_queue.models import Job, JobStatus, JobType


def test_settings_load_from_environment(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("IMAP_HOST", "imap.example.com")
    monkeypatch.setenv("IMAP_USERNAME", "quotes@example.com")
    monkeypatch.setenv("IMAP_PASSWORD", "test-password")

    settings = EmailSettings.from_env()

    assert settings.imap_host == "imap.example.com"
    assert settings.imap_port == 993
    assert settings.imap_password.get_secret_value() == "test-password"
    assert settings.ollama_model == "llama3.1:8b"


def test_settings_requires_credentials(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    for name in ("IMAP_HOST", "IMAP_USERNAME", "IMAP_PASSWORD"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValueError, match="IMAP_HOST, IMAP_USERNAME, IMAP_PASSWORD"):
        EmailSettings.from_env()


def test_models_validate_and_provide_safe_defaults():
    detected = DetectedEmail(uid=42, mailbox="INBOX")
    job = Job(job_type=JobType.EMAIL_RECEIVED, email_uid=detected.uid, mailbox=detected.mailbox)

    assert job.status is JobStatus.PENDING
    assert job.payload == {}
    assert job.attempts == 0


def test_models_reject_invalid_identifiers():
    with pytest.raises(ValidationError):
        DetectedEmail(uid=0, mailbox="INBOX")

    with pytest.raises(ValidationError):
        Job(job_type=JobType.EMAIL_RECEIVED, email_uid=-1, mailbox="INBOX")
