"""Repair MIME-encoded sender and subject values already stored in the database.

Usage:
    uv run python -m scripts.repair_email_encoding --dry-run
    uv run python -m scripts.repair_email_encoding
"""
import argparse
import json
import os
from pathlib import Path

from db_contexts.models import RetrievedEmail
from db_contexts.sessions import SessionLocal
from email_retriever.retriever import _decode_mime_header


def repair_email_encoding(dry_run: bool = False) -> int:
    data_dir = Path(os.getenv("DATA", "data"))
    repaired = 0

    with SessionLocal() as session:
        emails = session.query(RetrievedEmail).order_by(RetrievedEmail.id).all()
        updates: list[tuple[RetrievedEmail, str, str]] = []

        for email_row in emails:
            decoded_from = _decode_mime_header(email_row.from_email)
            decoded_subject = _decode_mime_header(email_row.subject)
            if (
                decoded_from != email_row.from_email
                or decoded_subject != email_row.subject
            ):
                updates.append((email_row, decoded_from, decoded_subject))

        if not dry_run:
            for email_row, decoded_from, decoded_subject in updates:
                email_row.from_email = decoded_from
                email_row.subject = decoded_subject
            session.commit()

        for email_row, decoded_from, decoded_subject in updates:
            artifact = data_dir / "emails" / f"{email_row.email_id}_email.json"
            if artifact.exists() and not dry_run:
                payload = json.loads(artifact.read_text(encoding="utf-8"))
                payload["from"] = decoded_from
                payload["subject"] = decoded_subject
                artifact.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=4) + "\n",
                    encoding="utf-8",
                )
            print(
                f"{'would repair' if dry_run else 'repaired'} "
                f"email_id={email_row.email_id}: {decoded_subject}"
            )
            repaired += 1

    print(
        f"{'would repair' if dry_run else 'repaired'} "
        f"{repaired} email(s)"
    )
    return repaired


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the records that would change without writing anything",
    )
    args = parser.parse_args()
    repair_email_encoding(dry_run=args.dry_run)
