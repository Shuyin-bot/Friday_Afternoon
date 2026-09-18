# Review UI

A small FastAPI app that exposes the `queued_jobs` / `retrieved_email` tables
as JSON and serves a single-page dashboard, so a non-technical reviewer can
inspect what the agent workflow produced without a terminal or `sqlite3`.

This is a **read-mostly internal tool**, not a public API: no auth, no rate
limiting, intended for local/dev review only.

## Run it

```bash
uv run uvicorn api.main:app --reload --port 8000
```

- Dashboard: http://localhost:8000/
- Swagger / OpenAPI docs: http://localhost:8000/docs

In GitHub Codespaces, port `8000` will be auto-forwarded; open it from the
**Ports** tab. This is the first port in this project that actually belongs
to our own code — every other port you may see in the Codespaces Ports panel
comes from the Codespaces/VS Code infrastructure itself, not this project.

## What the dashboard shows

- A status funnel (`PENDING` -> `CLASSIFIED` -> `EXTRACTED` ->
  `RESEARCH_EXT` -> `RESEARCH_INT` -> `DRAFTED` / `COMPLETED`).
- A job table (sender, subject, status, created time).
- A detail panel per job: the original email body, the classification
  result and reason, extracted fields, external/internal research (or the
  reason a stage was skipped), and the generated draft subject/body.
- Two buttons that trigger `email_retriever.retriever` and
  `agents_workflow.workflow` in the background (equivalent to running the
  `uv run python -m ...` commands from the README, just from the browser).

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/stats` | Job counts per status |
| GET | `/api/jobs` | List jobs, optional `?status=` filter |
| GET | `/api/jobs/{id}` | Full detail for one job |
| POST | `/api/run/retrieve` | Start the IMAP retriever in the background |
| POST | `/api/run/workflow` | Start the agent workflow in the background |

`meta_data` is stored as a JSON object whose values are themselves
`model_dump_json()` strings. The API decodes that extra layer server-side, so
both `/docs` and the dashboard return real nested objects instead of escaped
JSON strings.

## Switching the LLM provider or model

The pipeline's LLM is fully configured through `.env` and
`agents_workflow/provider/base_provider.py` — no other code needs to change.

```env
LLM_PROVIDER=openrouter
LLM_MODEL=google/gemini-3.5-flash
LLM_API_KEY=sk-or-...
```

To try a different model on OpenRouter (for example DeepSeek), only the
model name changes:

```env
LLM_MODEL=deepseek/deepseek-v4-flash
```

Supported `LLM_PROVIDER` values: `google`, `openai`, `ollama`, `groq`,
`openrouter`. Model names must use whatever prefix the provider requires
(OpenRouter requires an upstream prefix such as `google/` or `deepseek/`).

## Known limitations / next steps

- Read-mostly: there is no approve/reject action yet. Adding one requires a
  new `QueuedJob` status (e.g. `APPROVED` / `REJECTED`) and an Alembic
  migration — intentionally left out of this first version to avoid a schema
  change under time pressure.
- The "run" buttons block on a background task with a fixed client-side
  wait; for a long-running mailbox fetch you may need to refresh manually.
- No authentication. Do not expose this port outside a trusted/dev network.
