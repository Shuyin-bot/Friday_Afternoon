# Agent Workflow

The workflow entry point is:

```text
agents_workflow/workflow.py
```

Run it with:

```bash
uv run python -m agents_workflow.workflow
```

## Processing flow

```text
PENDING
   |
   +--> classifier --> NOT_QUOTATION
   |
   +--> classifier --> CLASSIFIED --> core quotation agent --> DRAFTED
                                      |                         |
                                      |                         +--> COMPLETED
                                      |                         +--> CLASSIFIED
                                      |                              (review feedback)
                                      |
                                      +--> WAITING_FOR_INPUT
                                             |
                                  human answer + session resume
                                             |
                                      CLASSIFIED

Any unhandled agent error --> FAILED
```

The classifier is responsible only for deciding whether an email is a
quotation request. Non-quotation messages become `NOT_QUOTATION`; they are not
treated as completed quotations.

The core agent is a PydanticAI agent with typed `QuotationDraftOutput`. It can
choose the tools it needs for:

- Email detail extraction
- Product catalogue lookup
- Company research memory lookup
- External company research
- Company research persistence
- Price calculation
- Draft generation
- Human input requests

The workflow does not force a fixed tool order.

## Agent sessions

Each quotation job has one row in `agent_sessions`, keyed by
`queued_job_id`. The session stores:

- Current session status
- Current workflow step
- Summary and context JSON
- Serialized PydanticAI message history
- Last error, if any

On a new job, the workflow creates an active session. On a resumed job, it
loads the existing session and passes the stored message history back to
PydanticAI.

## Human-in-the-loop flow

When the core agent calls `request_human_input`:

1. A `human_requests` row is created.
2. The current agent checkpoint is saved.
3. PydanticAI cancellation closes the interrupted tool call in the saved
   message history.
4. The session becomes `WAITING_FOR_HUMAN`.
5. The job becomes `WAITING_FOR_INPUT`.

After the human answers through the API:

1. The request becomes `ANSWERED`.
2. The answer is saved in the session summary.
3. The session becomes `READY_TO_RESUME`.
4. The job returns to `CLASSIFIED`.

The next workflow run restores the session history and adds the human answer as
the next prompt. The agent can then continue, request more input, or produce a
draft.

## Draft review flow

Drafted quotation jobs can be reviewed through the API/frontend:

```text
DRAFTED --approve--> COMPLETED
DRAFTED --edit-----> DRAFTED
DRAFTED --reject---> COMPLETED
DRAFTED --comment--> CLASSIFIED
```

Reviewer comments are stored in the job metadata and session summary. A later
workflow run resumes the session with that feedback and generates a revised
draft.

## Persistence boundaries

- Email metadata and job state live in SQLite.
- Email bodies remain JSON artifacts under `data/emails/`.
- Product details, prices, and inventory use SQLite as the source of truth.
- Chroma stores product embeddings for semantic fallback search.
- Agent session state and message history live in SQLite.

The workflow is a sequential command, not a continuously running worker. The
API can start it as a background task, but scheduling and process supervision
are still outside the current scope.
