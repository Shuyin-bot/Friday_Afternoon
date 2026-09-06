# Maintenance Guide

This guide describes how to change the project safely.

## Before Editing

1. Read the relevant package and its milestone tests.
2. Run the complete suite:

   ```bash
   uv run --extra dev pytest
   ```

3. Check the current branch and worktree:

   ```bash
   git status --short --branch
   ```

4. Confirm whether the change belongs to an existing milestone or should be added to the roadmap.

Do not overwrite unrelated working-tree changes.

## Layer Ownership Rules

### Email Detection

`email_detection_layer` may:

- Talk to IMAP.
- Parse and normalize email data.
- Persist email artifacts and ingestion state.
- Create queue jobs through an injected queue dependency.

It must not:

- Call Ollama or PydanticAI.
- Decide whether a quote should be sent.
- Send email.
- Contain product-pricing rules.

### Queue

`job_queue` may:

- Persist jobs.
- Claim jobs.
- Apply leases and retries.
- Dispatch registered handlers.

It must not:

- Parse email bodies.
- Know agent prompts.
- Make business decisions.
- Bypass the worker lease.

### Agents

`agent_system` may:

- Define Python agent behavior.
- Validate agent inputs and outputs.
- Record execution results.
- Use injected dependencies when a future milestone permits tools.

It must not:

- Treat email text as system instructions.
- Grant itself new tools.
- Send outbound email without a future explicit approval boundary.
- Calculate authoritative prices using an LLM.

## Adding a New Agent

1. Define a Pydantic input model.
2. Define a Pydantic output model.
3. Implement a Python class with:

   ```python
   metadata = AgentMetadata(...)
   input_model = InputModel
   output_model = OutputModel

   async def run(self, context: AgentContext) -> OutputModel:
       ...
   ```

4. Register the agent explicitly with `AgentRegistry`.
5. Add a job-type mapping only if the agent should consume queue jobs.
6. Test valid output, invalid input, invalid output, and failure recording.
7. Keep external services behind injected dependencies.

Do not put a large general-purpose prompt in one agent. Give each agent one responsibility and the minimum permissions it needs.

## Adding a Queue Job Type

1. Add the value to `JobType`.
2. Define the job payload contract with Pydantic.
3. Define which component creates it.
4. Define which worker handles it.
5. Decide whether duplicate jobs for the same email are allowed.
6. Add tests for enqueueing, claiming, completion, retries, and dead letters.
7. Document the transition in `docs/architecture.md` and `plan.md`.

The current queue uniqueness rule is one job per `(job_type, mailbox, email_uid)`. If a job needs a different identity rule, change the schema and tests deliberately rather than bypassing idempotency.

## Changing SQLite Schemas

The current project creates tables with `CREATE TABLE IF NOT EXISTS`; it does not yet have a migration framework. For local development, schema changes can be tested with a fresh temporary database.

For a deployed or shared database, do not silently change a table definition. Before adding persistent usage:

- Add explicit migrations.
- Version the schema.
- Back up the database.
- Test migration and rollback behavior.
- Decide how old job and artifact records are retained.

## Testing External Integrations

Unit tests must not depend on:

- A personal Gmail mailbox.
- A real password.
- Ollama being installed or running.
- Internet availability.
- A production database.

Use fakes and temporary directories, following the existing fake IMAP tests. Add separate manual or opt-in integration tests only when the test account and credentials are configured safely.

## Debugging an Ingestion Failure

Check in this order:

1. Configuration:

   ```bash
   uv run email-detect
   ```

2. Ingestion logs:

   ```bash
   less logs/ingest.log
   ```

3. Email state:

   ```bash
   sqlite3 data/email_state.db \
     "SELECT mailbox, uid, status, error FROM email_messages ORDER BY uid;"
   ```

4. Queue state:

   ```bash
   sqlite3 data/email_state.db \
     "SELECT id, job_type, status, attempts, last_error FROM jobs ORDER BY created_at;"
   ```

5. Artifact existence under `DATA_DIR`.

Common causes include an invalid Gmail App Password, IMAP disabled by an administrator, a missing artifact file, a stale local database, and an overlapping cron invocation.

## Debugging an Agent Failure

Inspect the queue job and its agent runs:

```bash
sqlite3 data/email_state.db \
  "SELECT id, job_type, status, attempts, last_error FROM jobs ORDER BY created_at;"

sqlite3 data/email_state.db \
  "SELECT job_id, agent_name, status, error FROM agent_runs ORDER BY started_at;"
```

An agent failure should appear both as a failed `agent_runs` record and as a queue retry or dead-letter transition. If the queue job completes despite an agent failure, investigate the handler exception boundary before changing retry settings.

## Security Checklist

Before merging an integration or agent change, verify:

- No secret appears in the diff.
- No email content is interpolated into system instructions without a clear trust label.
- All tool inputs are schema-validated.
- Tool permissions are explicit.
- Attachments are not executed.
- Outbound email remains disabled unless human approval is implemented.
- Logs do not contain passwords, tokens, or unnecessary message contents.
- New external calls have timeouts and tests for failure.

## Pull Requests and CI

GitHub Actions runs `.github/workflows/ci.yml` for pull requests targeting `main` and for pushes to `main`.

Run locally what CI runs:

```bash
uv run --extra dev pytest
```

The protected `main` branch should require the `Tests` status check before merge. Keep the check deterministic; do not require a live mailbox, live Ollama instance, or live web search for ordinary pull requests.
