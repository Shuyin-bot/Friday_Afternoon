# Getting Started

## Requirements

- Python 3.11 or newer.
- `uv`.
- A test IMAP mailbox.
- A Gmail App Password when using Gmail.

## Install

From the repository root:

```bash
uv sync
```

## Configure

Create `.env` with values similar to:

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USERNAME=your-test-account@gmail.com
IMAP_PASSWORD=your-gmail-app-password
MAILBOX=INBOX
EMAIL_DB_PATH=data/emails.db
DATA=data
```

`EMAIL_DB_PATH` controls the SQLite database used by SQLAlchemy. `DATA`
controls where retrieved email JSON artifacts are written.

## Create the Database

Apply the schema migrations:

```bash
uv run alembic upgrade head
```

Verify the revision:

```bash
uv run alembic current
```

## Retrieve Emails

Run the retriever as a module:

```bash
uv run python -m email_retriever.retriever
```

Run it from the repository root. Running the file directly can cause imports
such as `db_contexts` to fail because Python changes the import path for direct
file execution.

New messages create:

```text
retrieved_email row
queued_jobs row with PENDING status
data/emails/<email_id>_email.json
```

Running the retriever again skips email IDs already present in the database.

## Inspect Results

```bash
sqlite3 data/emails.db ".tables"
sqlite3 data/emails.db "SELECT * FROM retrieved_email;"
sqlite3 data/emails.db "SELECT * FROM queued_jobs;"
```

List JSON artifacts:

```bash
find data/emails -type f -print
```

## Current Scope

The retriever currently reads email and creates queued work. It does not yet
consume jobs, classify messages, call an agent, perform semantic search, or
send email.
