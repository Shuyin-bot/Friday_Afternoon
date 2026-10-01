# Quotation Bot

Quotation Bot is currently a Python 3.11 proof of concept for retrieving
business emails and placing quotation-related work into an agentic workflow
that is being built with Pydantic and PydanticAI.

The current implementation focuses on:

- Reading email from an IMAP mailbox.
- Avoiding duplicate email records.
- Storing email metadata in SQLite.
- Creating a queued job for every new email.
- Saving the retrieved email body as a JSON artifact.
- Managing the database schema with SQLAlchemy and Alembic.
- Modeling products, aliases, warehouses, inventory, price lists, and prices
  for a packaging manufacturer.
- Loading product records into SQLite and a persistent local Chroma collection.
- Persisting agent sessions and PydanticAI message history for resumable work.
- Pausing for human input and resuming the core agent after an answer.
- Reviewing, editing, approving, or sending drafted quotations back for revision.

The agent workflow classifies pending emails, lets the core agent choose the
necessary extraction, research, product, pricing, and drafting tools, and
persists a resumable session for each quotation job. Human input pauses the
workflow; an answer requeues the job and resumes the agent with its saved
message history. Sending email is not implemented yet.

## Current Flow

```text
IMAP mailbox
    |
    v
email_retriever.retriever
    |
    +--> RetrievedEmail metadata in SQLite
    +--> QueuedJob with PENDING status
    +--> data/emails/<email_id>_email.json
    |
    v
agent workflow (agents_workflow.workflow)
    PENDING      --classify-->        CLASSIFIED
       |                                  |
       |                                  +--> DRAFTED
       +--> NOT_QUOTATION                 |
                                          +--> WAITING_FOR_INPUT
                                                   |
                              human answer --------+
                                                   |
                                             CLASSIFIED (resume)

    DRAFTED --approve--> COMPLETED
    DRAFTED --reject-->  COMPLETED
    DRAFTED --comment--> CLASSIFIED (resume with feedback)
    any agent error ---------------------> FAILED
```

`NOT_QUOTATION` is used for emails that are not quotation requests. `COMPLETED`
is reserved for quotation work that has been reviewed or rejected. Drafts and
review feedback are stored in `queued_jobs.meta_data`.

Each quotation job has one `agent_sessions` row. The session stores the current
step, summary, context, and serialized PydanticAI message history. This allows
the core agent to resume after human input or draft feedback instead of starting
from the original email again.

The email body is not stored in the `retrieved_email` table. It is written to a
JSON file so it can later be passed to an extraction or classification process.

## Review Dashboard

A FastAPI app under `api/` exposes the pipeline results as JSON and a
single-page dashboard, for reviewing results without a terminal:

```bash
uv run uvicorn api.main:app --reload --port 8000
```

Open `http://localhost:8000/` for the legacy local dashboard, or
`http://localhost:8000/docs` for the interactive API docs. The React frontend
lives in the sibling `friday_afternoon_fe/` project and uses the same API.
See [docs/ui.md](docs/ui.md) for details.

## Project Structure


```text
db_contexts/
├── base.py                         Shared SQLAlchemy declarative base
├── sessions.py                     Engine and SessionLocal
├── models/
│   ├── email_retriever_models.py   Email and queued-job models
│   ├── agent_session_models.py      Resumable agent sessions
│   ├── human_request_models.py      Human-in-the-loop requests
│   ├── product_models.py           Product and packaging data models
│   └── __init__.py                 Model exports for application and Alembic
└── repos/
    ├── agent_session_repository.py Session checkpoints and resumption
    ├── email_repository.py         Email deduplication and queue creation
    ├── human_request_repository.py Human answers and job requeueing
    └── product_repository.py       Product, inventory, and pricing queries

email_retriever/
└── retriever.py                    IMAP retrieval and JSON artifact creation

agents_workflow/
├── workflow.py                     Classification and resumable core workflow
└── agents/
    ├── classifier.py                Quotation email classifier
    ├── core_agent.py                Tool-using quotation agent
    ├── core_models.py               Agent dependencies and typed outputs
    └── tools/                       Research, pricing, drafting, and human input

migrations/
├── env.py                          Alembic metadata and database configuration
├── script.py.mako                  Migration file template
└── versions/                       Versioned schema changes

vector_contexts/
└── chroma.py                       Persistent Chroma client and products collection

mock_data/
├── product_seed.json                Dummy product, stock, and price data
└── leads/email_inbox.v1-demo.json   Seed lead set for scripts/seed_mock_leads.py

scripts/
├── load_product_data.py             Loads seed data into SQLite and Chroma
└── seed_mock_leads.py                Seeds the mock demo leads as if retrieved via IMAP
```

## Setup

Install the project dependencies:

```bash
uv sync
```

The project uses Python 3.11:

```bash
uv run python --version
```

Configure a local `.env` file. At minimum, email retrieval needs:

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

For Gmail, use an App Password rather than the normal account password.
Never commit `.env` or place credentials in source code.

## Database Migrations

Apply all migrations:

```bash
uv run alembic upgrade head
```

Check the current revision:

```bash
uv run alembic current
```

The current schema creates these tables:

```text
retrieved_email
queued_jobs
human_requests
agent_sessions
products
product_aliases
warehouses
inventory
price_lists
product_prices
```

Create a migration after changing SQLAlchemy models:

```bash
uv run alembic revision --autogenerate -m "describe the schema change"
```

Review an autogenerated migration before applying it. To roll back one
migration:

```bash
uv run alembic downgrade -1
```

The application does not call `Base.metadata.create_all()`. Alembic owns schema
creation and updates.

## Run Email Retrieval

Run the retriever from the repository root as a module:

```bash
uv run python -m email_retriever.retriever
```

The retriever:

1. Connects to the configured IMAP mailbox.
2. Searches for all messages, or only unseen messages when configured by the
   caller.
3. Filters out email IDs already stored in SQLite.
4. Fetches each new email.
5. Extracts plain-text content.
6. Inserts email metadata into `retrieved_email`.
7. Creates a `PENDING` row in `queued_jobs`.
8. Writes the email data to `data/emails/<email_id>_email.json`.

The module does not classify emails, call an LLM, or send replies.

## Run the Agent Workflow

After retrieving emails, run the workflow from the repository root:

```bash
uv run python -m agents_workflow.workflow
```

The workflow processes `PENDING` jobs one at a time for classification. It moves
non-quotation jobs to `NOT_QUOTATION` and sends quotation jobs to the core
agent in `CLASSIFIED`. The core agent decides which tools to use and creates a
typed quotation draft.

If the agent requests human input, the job becomes `WAITING_FOR_INPUT`. After
the human answers, the request repository atomically marks the session
`READY_TO_RESUME` and requeues the job as `CLASSIFIED`. Running the workflow
again resumes the saved agent session.

## Load Product Data

The sample packaging catalogue is defined in `mock_data/product_seed.json`.
Load it into SQLite and the Chroma products collection with:

```bash
uv run python -m scripts.load_product_data
```

The loader uses each SKU as the stable Chroma document ID and can be rerun for
existing products. Chroma stores product documents and embeddings as a semantic
fallback after SQL product lookup.

## Inspect the Database

If the SQLite command-line client is installed:

```bash
sqlite3 data/emails.db ".tables"
```

Inspect retrieved emails:

```bash
sqlite3 data/emails.db \
  "SELECT id, email_id, from_email, subject, created_at FROM retrieved_email;"
```

Inspect queued work:

```bash
sqlite3 data/emails.db \
  "SELECT id, email_id, status, created_at FROM queued_jobs;"
```

Inspect migration state:

```bash
sqlite3 data/emails.db "SELECT * FROM alembic_version;"
```

## Database Domain

The packaging-company catalogue contains:

- `Product`: SKU, name, category, box style, material, dimensions, and active
  status.
- `ProductAlias`: customer or sales terminology for a product.
- `Warehouse`: physical storage locations.
- `Inventory`: product quantities by warehouse.
- `PriceList`: named currency-specific price lists.
- `ProductPrice`: quantity-based prices with validity dates.

Repository functions are in:

```text
db_contexts/repos/product_repository.py
```

They currently support product creation, exact SKU/name/alias lookup, active
product listing, warehouse inventory lookup, and current quantity-based price
lookup.

## Important Boundaries

The current code intentionally separates:

```text
email retrieval
database persistence
database migrations
    resumable agent workflow
```

Email content is treated as external data. It is written to a JSON artifact and
is not used as a database instruction or schema definition.

## Current Limitations

- The workflow is a simple sequential runner, not a continuously running
  worker.
- Outbound email sending is not implemented yet.
- The React frontend is a separate sibling project and requires the FastAPI
  backend to be running.
- The retriever currently extracts plain text only.
- There is no automated test suite in the current working tree.

## Security

- Use a test mailbox during development.
- Use Gmail App Passwords for IMAP access.
- Keep `.env` out of version control.
- Do not commit customer emails or generated database files.
- Do not run retrieval against a production mailbox until the duplicate and
  failure behavior has been reviewed.
