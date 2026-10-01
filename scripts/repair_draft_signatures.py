"""Replace untouched placeholder signatures in stored quotation drafts.

Usage:
    uv run python -m scripts.repair_draft_signatures --dry-run
    uv run python -m scripts.repair_draft_signatures
"""
import argparse
import json
import re

from agents_workflow.agents.tools.draft_quotation_email_tool import _seller_signature
from db_contexts.models import JobStatus, QueuedJob
from db_contexts.sessions import SessionLocal


PLACEHOLDER_SIGNATURES = (
    re.compile(
        r"\[Your Name\]\n\[Your Position\]\n\[Company Name\]\n\[Contact Details\]"
    ),
    re.compile(r"\[Your Name\]\n\[Your Title\]\n\[Company\]\n\[Phone\]\n\[Email\]"),
)


def repair_draft_signatures(dry_run: bool = False) -> int:
    repaired = 0
    signature = _seller_signature()

    with SessionLocal() as session:
        jobs = session.query(QueuedJob).filter_by(status=JobStatus.DRAFTED).all()
        for job in jobs:
            metadata = json.loads(job.meta_data or "{}")
            draft = metadata.get("draft")
            if not isinstance(draft, str):
                continue

            draft_data = json.loads(draft)
            body = draft_data.get("body", "").replace("\r\n", "\n")
            if not any(pattern.search(body) for pattern in PLACEHOLDER_SIGNATURES):
                continue

            for pattern in PLACEHOLDER_SIGNATURES:
                body = pattern.sub(signature, body)
            draft_data["body"] = body
            if not dry_run:
                metadata["draft"] = json.dumps(draft_data, ensure_ascii=False)
                job.meta_data = json.dumps(metadata, ensure_ascii=False)
            repaired += 1
            print(f"{'would repair' if dry_run else 'repaired'} job_id={job.id}")

        if not dry_run:
            session.commit()

    print(f"{'would repair' if dry_run else 'repaired'} {repaired} draft(s)")
    return repaired


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show drafts that would change without writing anything",
    )
    args = parser.parse_args()
    repair_draft_signatures(dry_run=args.dry_run)
