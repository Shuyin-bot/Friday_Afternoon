"""Retrieve and normalize complete messages from an IMAP mailbox."""

from __future__ import annotations

import imaplib
from datetime import datetime, timezone
from email.message import Message
from email.parser import BytesParser
from email.policy import default
from email.utils import getaddresses, parsedate_to_datetime, parseaddr
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import DetectedEmail


class EmailRetrievalError(RuntimeError):
    """Raised when an IMAP message cannot be fetched or parsed."""


class EmailAttachment(BaseModel):
    """Attachment extracted from an email message."""

    model_config = ConfigDict(frozen=True)

    filename: str | None = None
    content_type: str = Field(min_length=1)
    size: int = Field(ge=0)
    content: bytes | None = None


class RetrievedEmail(BaseModel):
    """Normalized email passed to classification and extraction agents."""

    model_config = ConfigDict(frozen=True)

    uid: int = Field(gt=0)
    message_id: str | None = None
    sender: str | None = None
    recipients: list[str] = Field(default_factory=list)
    subject: str | None = None
    received_at: datetime | None = None
    plain_text: str = ""
    html: str | None = None
    attachments: list[EmailAttachment] = Field(default_factory=list)
    raw_message: bytes


def fetch_raw_email(imap: imaplib.IMAP4_SSL, uid: int) -> bytes:
    """Fetch one complete RFC822 message by its stable IMAP UID."""
    if uid <= 0:
        raise ValueError("uid must be greater than zero")

    status, data = imap.uid("fetch", str(uid), "(RFC822)")
    if status != "OK" or not data:
        raise EmailRetrievalError(f"Unable to fetch IMAP message UID {uid}")

    for item in data:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            return item[1]
    raise EmailRetrievalError(f"IMAP returned no RFC822 content for UID {uid}")


def _decode_text(part: Message) -> str:
    """Decode a text MIME part without allowing bad bytes to abort retrieval."""
    payload = part.get_payload(decode=True)
    if payload is None:
        content = part.get_content()
        return content if isinstance(content, str) else ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _received_at(message: Message) -> datetime | None:
    """Parse the Date header and normalize timezone-less dates to UTC."""
    value = message.get("Date")
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _recipients(message: Message) -> list[str]:
    """Return addresses from To, Cc, and Bcc headers without display names."""
    headers = message.get_all("To", []) + message.get_all("Cc", []) + message.get_all("Bcc", [])
    return [address for _, address in getaddresses(headers) if address]


def _attachment(part: Message) -> EmailAttachment:
    """Convert one MIME attachment to a validated attachment model."""
    content = part.get_payload(decode=True) or b""
    return EmailAttachment(
        filename=part.get_filename(),
        content_type=part.get_content_type(),
        size=len(content),
        content=content,
    )


def parse_email(uid: int, raw_message: bytes) -> RetrievedEmail:
    """Parse raw RFC822 bytes into a normalized, immutable Pydantic model."""
    if not raw_message:
        raise EmailRetrievalError(f"IMAP message UID {uid} is empty")

    try:
        message = BytesParser(policy=default).parsebytes(raw_message)
        plain_text: str | None = None
        html: str | None = None
        attachments: list[EmailAttachment] = []

        parts = message.walk() if message.is_multipart() else [message]
        for part in parts:
            if part.is_multipart():
                continue
            disposition = part.get_content_disposition()
            filename = part.get_filename()
            if disposition == "attachment" or filename:
                attachments.append(_attachment(part))
                continue
            if part.get_content_type() == "text/plain" and plain_text is None:
                plain_text = _decode_text(part)
            elif part.get_content_type() == "text/html" and html is None:
                html = _decode_text(part)

        if plain_text is None and not message.is_multipart() and message.get_content_type() == "text/plain":
            plain_text = _decode_text(message)
        if html is None and not message.is_multipart() and message.get_content_type() == "text/html":
            html = _decode_text(message)

        return RetrievedEmail(
            uid=uid,
            message_id=message.get("Message-ID"),
            sender=parseaddr(message.get("From", ""))[1] or None,
            recipients=_recipients(message),
            subject=message.get("Subject"),
            received_at=_received_at(message),
            plain_text=plain_text or "",
            html=html,
            attachments=attachments,
            raw_message=raw_message,
        )
    except (TypeError, ValueError, UnicodeError) as error:
        raise EmailRetrievalError(f"Unable to parse IMAP message UID {uid}") from error


def retrieve_email(imap: imaplib.IMAP4_SSL, email: DetectedEmail) -> RetrievedEmail:
    """Fetch and parse a detected email from its selected IMAP mailbox."""
    raw_message = fetch_raw_email(imap, email.uid)
    return parse_email(email.uid, raw_message)
