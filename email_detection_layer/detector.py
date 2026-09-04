"""IMAP connection primitives for the email detection layer."""

from __future__ import annotations

import imaplib
from email import policy
from email.parser import BytesParser
import logging
from typing import Any

from .config import EmailSettings
from .models import DetectedEmail
from .retriever import fetch_raw_email
from .state import EmailStateStore

logger = logging.getLogger(__name__)


class ImapConnectionError(RuntimeError):
    """Raised when the detector cannot connect, authenticate, or select a mailbox."""


def establish_connection(settings: EmailSettings) -> tuple[bool, imaplib.IMAP4_SSL | None]:
    """Open and prepare an authenticated IMAP connection.

    The boolean return value is retained for the small command-line experiment. The
    higher-level detection function raises :class:`ImapConnectionError` so callers
    receive a useful failure instead of silently skipping a mailbox.
    """
    try:
        imap = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        status, _ = imap.login(settings.imap_username, settings.imap_password.get_secret_value())
        if status != "OK":
            raise ImapConnectionError("IMAP authentication failed")
        status, _ = imap.select(settings.mailbox)
        if status != "OK":
            raise ImapConnectionError(f"Unable to select mailbox {settings.mailbox!r}")
    except (OSError, imaplib.IMAP4.error, ImapConnectionError):
        try:
            imap.logout()
        except (UnboundLocalError, OSError, imaplib.IMAP4.error):
            pass
        return False, None
    return True, imap


def fetch_email(imap: imaplib.IMAP4_SSL, email_id: bytes) -> Any:
    """Fetch and parse one RFC822 message through the retrieval layer."""
    raw_data = fetch_raw_email(imap, int(email_id))
    return BytesParser(policy=policy.default).parsebytes(raw_data)


def check_new_emails(imap: imaplib.IMAP4_SSL) -> list[DetectedEmail]:
    """Return all message UIDs currently visible in the selected mailbox.

    This low-level helper searches from UID 1. Use :func:`detect_new_emails` for
    normal operation, where the caller supplies the last successfully processed UID.
    """
    return check_new_emails_since(imap, mailbox="INBOX", last_uid=0)


def check_new_emails_since(
    imap: imaplib.IMAP4_SSL,
    mailbox: str,
    last_uid: int = 0,
) -> list[DetectedEmail]:
    """Search for message UIDs greater than `last_uid` in the selected mailbox."""
    if last_uid < 0:
        raise ValueError("last_uid cannot be negative")

    status, data = imap.uid("search", None, f"UID {last_uid + 1}:*")
    if status != "OK":
        raise RuntimeError("IMAP UID search failed")

    raw_uids = data[0].split() if data and data[0] else []
    detected: list[DetectedEmail] = []
    for raw_uid in raw_uids:
        uid = int(raw_uid)
        if uid > last_uid:
            detected.append(DetectedEmail(uid=uid, mailbox=mailbox))
    return detected


def detect_new_emails(settings: EmailSettings, last_uid: int = 0) -> list[DetectedEmail]:
    """Authenticate to IMAP, detect new UIDs, and close the connection safely.

    State persistence is deliberately not handled here; M3 will provide the
    persistent cursor. `last_uid` therefore comes from the caller for now.
    """
    connected, imap = establish_connection(settings)
    if not connected or imap is None:
        raise ImapConnectionError(
            f"Unable to connect or authenticate to {settings.imap_host}:{settings.imap_port}"
        )

    try:
        detected = check_new_emails_since(imap, settings.mailbox, last_uid)
        logger.info("Detected %d new email(s) in %s", len(detected), settings.mailbox)
        return detected
    finally:
        try:
            imap.logout()
        except (OSError, imaplib.IMAP4.error):
            logger.warning("Unable to cleanly close the IMAP connection", exc_info=True)


def main() -> None:
    """Detect and record new messages from the configured mailbox."""
    settings = EmailSettings.from_env()
    state = EmailStateStore(settings.state_db_path)
    try:
        last_uid = state.get_last_queued_uid(settings.mailbox)
        for email in detect_new_emails(settings, last_uid):
            if state.record_detected(email):
                print(email.model_dump_json())
    finally:
        state.close()


if __name__ == "__main__":
    main()
