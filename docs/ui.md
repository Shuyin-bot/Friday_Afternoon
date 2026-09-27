# Review UI and API

The FastAPI application exposes the quotation pipeline for local review. The
React frontend is maintained separately in the sibling directory:

```text
../quotation_bot_frontend/
```

The API is intended for local development only. It has no authentication or
rate limiting.

## Run the backend

```bash
uv run uvicorn api.main:app --reload --port 8000
```

- API: http://localhost:8000/
- Swagger: http://localhost:8000/docs

## Run the React frontend

In a second terminal:

```bash
cd ../quotation_bot_frontend
npm install
npm run dev
```

Open the Vite URL, normally http://localhost:5173. Vite proxies `/api` calls
to FastAPI on port `8000`.

The frontend provides:

- Status cards for classification, human review, in-progress, completed, and
  non-quotation jobs
- Horizontal status-card scrolling and activity pagination
- Live dashboard updates through Server-Sent Events
- Job detail pages with the original email, draft, metadata, and human review
- Draft approval, editing, rejection, and reviewer feedback
- Manual email retrieval and workflow controls

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/stats` | Job counts per status |
| GET | `/api/events` | SSE stream for job-count changes |
| GET | `/api/jobs` | List jobs, optional `?status=` filter |
| GET | `/api/jobs/{id}` | Full detail for one job |
| POST | `/api/jobs/{id}/approve` | Approve a drafted quotation |
| PUT | `/api/jobs/{id}/draft` | Edit a drafted quotation |
| POST | `/api/jobs/{id}/reject` | Reject and close a draft |
| POST | `/api/jobs/{id}/review-comment` | Send a draft back with feedback |
| GET | `/api/human-requests` | List pending human requests |
| GET | `/api/human-requests/{id}` | Get one human request |
| POST | `/api/human-requests/{id}/answer` | Answer and requeue a request |
| POST | `/api/run/retrieve` | Start IMAP retrieval in the background |
| POST | `/api/run/workflow` | Start the agent workflow in the background |

## Human answer behavior

`POST /api/human-requests/{id}/answer` performs the resume transition in one
repository transaction:

```text
human request -> ANSWERED
agent session -> READY_TO_RESUME
queued job    -> CLASSIFIED
```

The next workflow run resumes the stored PydanticAI message history.

## Draft feedback behavior

`POST /api/jobs/{id}/review-comment` stores the reviewer comment, sets the
session to `READY_TO_RESUME`, and returns the job to `CLASSIFIED`. Running the
workflow again gives the core agent the reviewer feedback and the previous
conversation.

## Live updates

The frontend connects to `/api/events` using `EventSource`. FastAPI emits a
`job_status` event whenever the job-count snapshot changes. The stream sends
periodic heartbeats and automatically reconnects through the browser's native
SSE behavior.

## Security limitations

Do not expose this API outside a trusted development network. It currently has
no authentication, authorization, or outbound-email safeguards.
