# Architecture

## Runtime Components

```text
cron
  |
  v
email_detection_layer.pipeline
  |
  +--> IMAP server
  +--> EmailStateStore (SQLite)
  +--> EmailArtifactStore (data/emails)
  +--> SQLiteJobQueue (SQLite)
          |
          v
      EMAIL_RECEIVED job
          |
          v
      agent_system.AgentWorker
          |
          v
      AgentRunner -> registered Python agent
          |
          v
      AgentRunStore (agent_runs table)
```

The pipeline and worker are separate processes. The pipeline is short-lived and cron starts it. The worker can run independently and spend time processing jobs.

## Repository Map

### `email_detection_layer/`

Owns the email-provider boundary and ingestion state.

- `config.py`: loads and validates environment variables into `EmailSettings`.
- `models.py`: Pydantic email detection contracts such as `DetectedEmail`.
- `detector.py`: opens IMAP, authenticates, selects a mailbox, and searches by UID.
- `retriever.py`: fetches RFC822 messages and creates `RetrievedEmail` models.
- `state.py`: stores mailbox cursors and per-email processing state.
- `storage.py`: saves raw `.eml` and normalized JSON artifacts.
- `pipeline.py`: coordinates one cron ingestion cycle.

This package must not call an LLM or choose quotation workflow decisions.

### `job_queue/`

Owns asynchronous job lifecycle mechanics.

- `models.py`: `Job`, `JobType`, `JobStatus`, and `ClaimedJob`.
- `repository.py`: SQLite persistence, idempotency, atomic claims, leases, retries, and dead letters.
- `dispatcher.py`: maps job-type strings to Python handlers.
- `worker.py`: claims jobs, invokes the dispatcher, and completes or fails jobs.

This package should not know about Gmail, quotation business rules, or specific agents.

### `agent_system/`

Owns Python agent execution.

- `models.py`: agent context, metadata, risk levels, and execution records.
- `base.py`: `BaseAgent` protocol.
- `registry.py`: explicit agent registration and lookup.
- `runner.py`: validates inputs and outputs and records execution results.
- `runs.py`: persists agent execution records in SQLite.
- `classifier.py`: deterministic M7 classifier stub.
- `worker.py`: adapts queue jobs to registered agents.

M8 provides the provider-neutral LLM boundary:

- `llm/config.py`: `LLMProvider` and `LLMSettings` loaded from `LLM_*` environment variables.
- `llm/factory.py`: constructs the correct PydanticAI model for Ollama, Groq, Gemini, Anthropic, or OpenAI.
- `llm_classifier.py`: uses the factory but does not know which provider is active.
- `ollama.py`: compatibility aliases for older Ollama-specific callers.

Ollama and OpenAI use the OpenAI-compatible chat model. Groq, Gemini, and Anthropic use native PydanticAI providers. Model construction is local and does not make a network request; network access begins only when an agent runs.

Change providers by changing configuration, not agent code:

```env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
LLM_API_KEY=gsk_your_key
```

Hosted provider credentials must never be logged or committed.

### `tests/`

Tests are organized by milestone:

- `test_m1.py`: configuration and model foundations.
- `test_m2.py`: IMAP detection.
- `test_m3.py`: email state.
- `test_m4.py`: retrieval and parsing.
- `test_m5.py`: queue lifecycle.
- `test_m6.py`: ingestion pipeline.
- `test_m7.py`: agent framework.

## Data Flow

### 1. Detection

`EmailIngestionPipeline.run()` asks `EmailStateStore` for the last queued UID. It then calls `check_new_emails_since()` with that UID. IMAP returns stable message UIDs, not message bodies.

New UIDs are inserted into `email_messages` with status `DETECTED`. Existing UIDs are ignored so repeated cron runs are safe.

### 2. Retrieval

For each retryable email, `retrieve_email()` calls IMAP `UID FETCH` with `(RFC822)`. `parse_email()` turns the bytes into a `RetrievedEmail` Pydantic model containing headers, text, HTML, attachments, and the original bytes.

Email content is data, not instructions. Parsing must never execute attachments or follow links.

### 3. Artifact Persistence

`EmailArtifactStore.save()` writes:

```text
data/emails/raw/<safe-message-id>-<uid>.eml
data/emails/normalized/<safe-message-id>-<uid>.json
```

The normalized JSON encodes attachment bytes as base64. The queue payload contains paths to these artifacts rather than duplicating the whole email in the job row.

### 4. Queue Insertion

The pipeline creates an `EMAIL_RECEIVED` `Job`. SQLite prevents duplicate jobs for the same `(job_type, mailbox, email_uid)` tuple.

Only after `queue.enqueue(job)` succeeds does the pipeline call `state.mark_queued(email)`. That method changes the email status to `QUEUED` and advances the mailbox cursor. If retrieval or enqueue fails, the email remains retryable and the cursor does not move past it.

### 5. Agent Execution

The queue worker claims a job and supplies a lease. `AgentWorker` maps the job type to an agent name. `AgentRunner`:

1. Looks up the agent in `AgentRegistry`.
2. Validates `context.input_data` with the agent's input model.
3. Calls the Python agent.
4. Validates the returned model with the agent's output model.
5. Saves a completed or failed `AgentExecutionRecord`.

Queue completion remains separate from agent audit logging. A runner failure is raised to `QueueWorker`, which applies queue retry rules.

### 6. Workflow Orchestration

`QuotationWorkflow` is the M9 stage coordinator. It is deliberately explicit Python code rather than a prompt asking one model to manage its own workflow. `WorkflowWorker` registers the coordinator as the handler for `EMAIL_RECEIVED` and all configured agent stages.

Each stage validates its result with a Pydantic model before saving it into `workflow_state` and creating the next queue job. The coordinator stops instead of guessing when:

- Classification says the message is not a quotation.
- Classification produces security flags.
- Classification confidence is below the configured threshold.
- Required quotation fields are missing.
- Sender verification is incomplete or requires review.
- Product research needs tools or has unresolved products.

The current M9 stub agents demonstrate the transitions without external services. They do not provide real sender identity checks, product data, pricing, or outbound email.

## State Machines

### Email state

```text
DETECTED -> RETRIEVED -> QUEUED -> PROCESSING -> COMPLETED
     \          \            \                    /
      +----------+------------+----> FAILED ------+
```

`FAILED` records remain eligible for ingestion retry. `EmailStateStore` owns this state.

### Job state

```text
PENDING -> RUNNING -> COMPLETED
              |
              +----> RETRYING -> RUNNING
              |
              +----> DEAD_LETTER
```

A worker lease makes a `RUNNING` job reclaimable after expiry. Jobs that exceed the queue's attempt limit are moved to `DEAD_LETTER`.

### Agent run state

```text
RUNNING -> COMPLETED
    |
    +----> FAILED
```

The execution record is written as `RUNNING` and updated in place when the attempt finishes.

## Trust Boundaries

Untrusted input includes:

- Email subjects and bodies.
- Attachments and extracted document text.
- Search results and web pages in future milestones.
- Tool responses in future milestones.

Trusted control includes:

- Python system code.
- Environment configuration.
- Pydantic schemas.
- Queue permissions.
- Agent tool allowlists.
- Human approval decisions.

Do not allow untrusted content to modify configuration, grant tools, change queue state, or trigger outbound email.
