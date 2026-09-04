from email_detection_layer.config import EmailSettings
from email_detection_layer.detector import detect_new_emails


class FakeImap:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.logged_in_with = None
        self.selected_mailbox = None
        self.search_arguments = None
        self.logged_out = False

    def login(self, username, password):
        self.logged_in_with = (username, password)
        return "OK", [b"authenticated"]

    def select(self, mailbox):
        self.selected_mailbox = mailbox
        return "OK", [b"0"]

    def uid(self, command, charset, criteria):
        self.search_arguments = (command, charset, criteria)
        return "OK", [b"7 9 12"]

    def logout(self):
        self.logged_out = True
        return "BYE", [b"logged out"]


def settings():
    return EmailSettings(
        imap_host="imap.example.com",
        imap_username="quotes@example.com",
        imap_password="secret",
        mailbox="QUOTES",
    )


def test_detects_only_uids_after_last_processed(monkeypatch):
    connection = None

    def fake_connection(host, port):
        nonlocal connection
        connection = FakeImap(host, port)
        return connection

    monkeypatch.setattr("email_detection_layer.detector.imaplib.IMAP4_SSL", fake_connection)

    detected = detect_new_emails(settings(), last_uid=9)

    assert [email.uid for email in detected] == [12]
    assert detected[0].mailbox == "QUOTES"
    assert connection.logged_in_with == ("quotes@example.com", "secret")
    assert connection.selected_mailbox == "QUOTES"
    assert connection.search_arguments == ("search", None, "UID 10:*")
    assert connection.logged_out is True


def test_empty_search_returns_no_messages(monkeypatch):
    class EmptyImap(FakeImap):
        def uid(self, command, charset, criteria):
            return "OK", [b""]

    monkeypatch.setattr(
        "email_detection_layer.detector.imaplib.IMAP4_SSL",
        lambda host, port: EmptyImap(host, port),
    )

    assert detect_new_emails(settings(), last_uid=12) == []


def test_connection_failure_is_reported(monkeypatch):
    def fail_to_connect(host, port):
        raise OSError("network unavailable")

    monkeypatch.setattr("email_detection_layer.detector.imaplib.IMAP4_SSL", fail_to_connect)

    try:
        detect_new_emails(settings())
    except RuntimeError as error:
        assert "Unable to connect or authenticate" in str(error)
    else:
        raise AssertionError("Expected IMAP connection failure")
