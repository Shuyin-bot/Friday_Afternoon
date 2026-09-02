"""IMAP connection primitives for the email detection layer."""

from __future__ import annotations

import imaplib
from email import policy
from email.parser import BytesParser
from typing import Any

from .config import EmailSettings
from .models import DetectedEmail


def establish_connection(settings: EmailSettings) -> tuple[bool, imaplib.IMAP4_SSL | None]:
    """Open an IMAP TLS connection without authenticating or selecting a mailbox."""
    try:
        imap = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    except OSError:
        return False, None
    return True, imap


def fetch_email(imap: imaplib.IMAP4_SSL, email_id: bytes) -> Any:
    """Fetch and parse one RFC822 message; retrieval will be completed in M4."""
    status, data = imap.fetch(email_id, "(RFC822)")
    if status != "OK" or not data or not isinstance(data[0], tuple):
        raise RuntimeError(f"Unable to fetch IMAP message {email_id!r}")
    raw_data = data[0][1]
    return BytesParser(policy=policy.default).parsebytes(raw_data)


def check_new_emails(imap: imaplib.IMAP4_SSL) -> list[DetectedEmail]:
    """Return detected email references; UID search is implemented in M2."""
    pass


def main() -> None:
    """Validate detector configuration and establish a test connection."""
    settings = EmailSettings.from_env()
    connected, imap = establish_connection(settings)
    if not connected or imap is None:
        raise RuntimeError(f"Unable to connect to {settings.imap_host}:{settings.imap_port}")
    try:
        print(f"Connected to {settings.imap_host}:{settings.imap_port}")
    finally:
        imap.logout()


if __name__ == "__main__":
    main()
