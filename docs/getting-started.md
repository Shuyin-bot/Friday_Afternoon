# Getting Started

This guide is for someone setting up the project for the first time.

## Prerequisites

- Python 3.9 or newer.
- `uv` installed.
- A test mailbox if you intend to connect to IMAP.
- A Gmail app password if using Gmail with IMAP.

Do not use a production mailbox for the first experiment. The initial UID cursor is `0`, so the first ingestion run may inspect every message in the selected mailbox.

## Install

From the repository root:

```bash
uv sync --extra dev
```

This installs the project, Pydantic, PydanticAI, `python-dotenv`, and the test dependencies into the environment managed by `uv`.

## Configure IMAP

Copy `.env.example` to `.env` and replace the placeholders:

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USERNAME=your-test-account@gmail.com
IMAP_PASSWORD=your-gmail-app-password
MAILBOX=INBOX
STATE_DB_PATH=data/email_state.db
DATA_DIR=data
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
LLM_API_KEY=
```

For Gmail, `IMAP_PASSWORD` should be an App Password, not your normal account password. The `.env` file is ignored by Git. Never put credentials in Python source, tests, logs, or queue payloads.

## Run Tests

Run the complete suite:

```bash
uv run --extra dev pytest
```

Run a single milestone's tests:

```bash
uv run --extra dev pytest tests/test_m7.py -v
```

The tests use fake IMAP connections, temporary SQLite databases, and deterministic agents. They do not need Gmail, Ollama, or internet access.

## Run the Detector

The detector verifies configuration, opens IMAP, and prints detected UID references:

```bash
uv run email-detect
```

The detector CLI uses the persistent UID cursor from `STATE_DB_PATH`. It does not retrieve messages into the queue; that is the ingestion pipeline's responsibility.

## Run One Ingestion Cycle

The ingestion command performs one complete M6 cycle:

```bash
uv run email-ingest
```

It:

1. Opens and authenticates an IMAP connection.
2. Reads the last queued UID from SQLite.
3. Searches for newer message UIDs.
4. Records newly discovered messages.
5. Fetches and parses each message.
6. Saves `.eml` and normalized `.json` artifacts under `DATA_DIR`.
7. Creates an `EMAIL_RECEIVED` job.
8. Marks the email queued and advances the cursor.
9. Logs out and exits.

It does not run an agent and does not send email.

## Inspect Results

List persisted artifacts:

```bash
find data/emails -type f -print
```

If SQLite is installed, inspect email state:

```bash
sqlite3 data/email_state.db \
  "SELECT mailbox, uid, status, error FROM email_messages ORDER BY uid;"
```

Inspect queue jobs:

```bash
sqlite3 data/email_state.db \
  "SELECT id, job_type, status, email_uid, mailbox, attempts FROM jobs ORDER BY created_at;"
```

The M6 jobs will normally remain `PENDING` until a worker is configured to handle their job type.

## Run the M9 Workflow

M9 provides `QuotationWorkflow` and `WorkflowWorker`. The workflow worker consumes queue jobs, loads normalized email artifacts for `EMAIL_RECEIVED`, and runs the configured Python agents for each later stage. A production worker command is not provided yet; construct the worker with an `SQLiteJobQueue`, `AgentRunner`, `WorkflowStore`, and explicit agent mapping. The complete behavior is demonstrated in `tests/test_m9.py`.

The M9 stub path is intentionally conservative:

```text
EMAIL_RECEIVED
  -> CLASSIFY_EMAIL
  -> EXTRACT_QUOTATION
  -> VERIFY_SENDER
  -> RESEARCH_PRODUCTS
  -> PREPARE_QUOTE
  -> GENERATE_DRAFT
  -> NEEDS_HUMAN_REVIEW
```

The default sender verifier requires human review, and the default product researcher reports that tooling is required. M10 will add controlled product and research tools. No M9 path sends email.

## Run from Cron

Create a log directory:

```bash
mkdir -p logs data
```

Add this to `crontab -e`:

```cron
*/5 * * * * cd /absolute/path/to/quotation_bot && flock -n /tmp/quotation-agent-ingest.lock .venv/bin/python -m email_detection_layer.pipeline >> logs/ingest.log 2>&1
```

`flock` prevents two slow ingestion runs from overlapping. Use absolute paths because cron has a minimal environment and does not necessarily load your interactive shell configuration.

View logs with:

```bash
less logs/ingest.log
```

## Run the M7 Stub Agent

M7 is currently demonstrated by enqueueing a `CLASSIFY_EMAIL` job directly and mapping that job to `quotation_classifier_stub`. See `tests/test_m7.py` for the executable example.

The stub is intentionally deterministic. It identifies quotation-related keywords and flags a small set of prompt-injection phrases. It does not contact Ollama and is not a production classifier.

## Test Ollama Integration

Install and start Ollama separately, then pull the configured model:

```bash
ollama pull llama3.1:8b
ollama serve
```

M8 uses a provider-neutral factory. Ollama is configured through `LLM_PROVIDER=ollama` and uses the OpenAI-compatible endpoint at `LLM_BASE_URL/v1`. The real classifier is created with `PydanticAIQuotationClassifier`; its output is validated as `QuotationClassification`.

Hosted provider examples:

```env
# Groq
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
LLM_API_KEY=gsk_your_key

# Gemini
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=your_google_key

# Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku-latest
LLM_API_KEY=your_anthropic_key
```

The M8 tests inject a fake PydanticAI client, so normal CI does not need any provider service.

Do not test the real model with customer emails or production data. Use a fixture mailbox and review the model's output before connecting it to workflow transitions.

## Stop and Reset Local State

To reset the local proof of concept, stop cron first, then remove only local generated data:

```bash
rm -rf data logs
```

Do not run this against a shared or production data directory. The command removes raw emails, normalized messages, queue jobs, and state.
