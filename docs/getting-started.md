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
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=your-api-key
CHROMA_PATH=data/chroma
CHROMA_PRODUCT_COLLECTION=products
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

## Load Product Data

Apply the migrations first, then load the sample packaging catalogue:

```bash
uv run python -m scripts.load_product_data
```

This stores product, inventory, and pricing records in SQLite and product
documents with local embeddings in Chroma.

## Run the Agent Workflow

```bash
uv run python -m agents_workflow.workflow
```

The workflow processes pending jobs sequentially. It classifies each email and
extracts quotation details from quotation requests, saving each result in the
job metadata and advancing its status.

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

The retriever only reads email and creates queued work. Agent processing is run
separately by `agents_workflow.workflow`; semantic querying, review, and email
sending are not implemented yet.
