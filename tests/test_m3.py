from email_detection_layer.models import DetectedEmail
from email_detection_layer.state import EmailProcessingStatus, EmailStateStore


def email(uid=10):
    return DetectedEmail(uid=uid, mailbox="INBOX")


def test_state_store_deduplicates_detected_messages(tmp_path):
    store = EmailStateStore(str(tmp_path / "state.db"))

    assert store.record_detected(email()) is True
    assert store.record_detected(email()) is False
    assert store.get_record(email()).status is EmailProcessingStatus.DETECTED
    assert store.get_last_queued_uid("INBOX") == 0

    store.close()


def test_cursor_advances_only_after_message_is_queued(tmp_path):
    store = EmailStateStore(str(tmp_path / "state.db"))
    message = email(11)
    store.record_detected(message)

    assert store.get_last_queued_uid("INBOX") == 0
    store.mark_queued(message)

    assert store.get_last_queued_uid("INBOX") == 11
    assert store.get_record(message).status is EmailProcessingStatus.QUEUED
    store.close()


def test_failed_message_can_be_retried(tmp_path):
    store = EmailStateStore(str(tmp_path / "state.db"))
    message = email(12)
    store.record_detected(message)
    store.set_status(message, EmailProcessingStatus.FAILED, "temporary IMAP error")

    assert store.can_enqueue(message) is True
    assert store.get_record(message).error == "temporary IMAP error"
    store.mark_queued(message)
    assert store.get_record(message).error is None
    store.close()
