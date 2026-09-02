from email.message import EmailMessage

import pytest

from email_detection_layer.models import DetectedEmail
from email_detection_layer.retriever import (
    EmailRetrievalError,
    RetrievedEmail,
    retrieve_email,
)


class FakeImap:
    def __init__(self, raw_message: bytes):
        self.raw_message = raw_message
        self.fetch_arguments = None

    def uid(self, command, uid, query):
        self.fetch_arguments = (command, uid, query)
        return "OK", [(b"header", self.raw_message)]


def make_message() -> bytes:
    message = EmailMessage()
    message["Message-ID"] = "<quote-123@example.com>"
    message["From"] = "Customer <customer@example.com>"
    message["To"] = "quotes@example.com"
    message["Cc"] = "sales@example.com"
    message["Subject"] = "Request for quotation"
    message["Date"] = "Tue, 02 Sep 2026 12:00:00 +0000"
    message.set_content("Please quote 10 routers.")
    message.add_alternative("<p>Please quote 10 routers.</p>", subtype="html")
    message.add_attachment(b"product,data\nrouter,10\n", maintype="text", subtype="csv", filename="products.csv")
    return message.as_bytes()


def test_retrieves_and_normalizes_multipart_email():
    imap = FakeImap(make_message())

    result = retrieve_email(imap, DetectedEmail(uid=17, mailbox="INBOX"))

    assert isinstance(result, RetrievedEmail)
    assert result.uid == 17
    assert result.message_id == "<quote-123@example.com>"
    assert result.sender == "customer@example.com"
    assert result.recipients == ["quotes@example.com", "sales@example.com"]
    assert result.subject == "Request for quotation"
    assert "10 routers" in result.plain_text
    assert "10 routers" in result.html
    assert result.attachments[0].filename == "products.csv"
    assert result.attachments[0].size > 0
    assert result.attachments[0].content is not None
    assert imap.fetch_arguments == ("fetch", "17", "(RFC822)")


def test_retrieves_single_part_plain_text_email():
    message = EmailMessage()
    message["From"] = "customer@example.com"
    message.set_content("A plain text request.")

    result = retrieve_email(FakeImap(message.as_bytes()), DetectedEmail(uid=2, mailbox="INBOX"))

    assert result.plain_text == "A plain text request.\n"
    assert result.html is None
    assert result.attachments == []


def test_empty_message_is_rejected():
    with pytest.raises(EmailRetrievalError, match="empty"):
        retrieve_email(FakeImap(b""), DetectedEmail(uid=3, mailbox="INBOX"))


def test_fetch_failure_is_reported():
    class FailedImap(FakeImap):
        def uid(self, command, uid, query):
            return "NO", [b"failed"]

    with pytest.raises(EmailRetrievalError, match="Unable to fetch"):
        retrieve_email(FailedImap(b"ignored"), DetectedEmail(uid=4, mailbox="INBOX"))
