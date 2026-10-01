# Command Cheatsheet

Every command you'll actually need for this project, grouped by scenario.
Unless noted otherwise, run these from the repo root (`Friday_Afternoon/`).

## Environment setup

```bash
uv sync                          # install Python dependencies
uv run alembic upgrade head       # create/upgrade the database schema
uv run alembic current            # check current schema revision
```

## Seed demo data and run the pipeline

```bash
uv run python -m scripts.seed_mock_leads            # seed (idempotent — reruns skip already-seeded leads)
uv run python -m scripts.seed_mock_leads --reset     # delete seeded pipeline rows and artifacts
uv run python -m scripts.repair_email_encoding --dry-run  # preview stored MIME header fixes
uv run python -m scripts.repair_email_encoding             # apply stored MIME header fixes
uv run python -m agents_workflow.workflow            # classify and run the resumable core quotation agent
```

If a run gets interrupted, run `agents_workflow.workflow` again. Jobs with an
existing `agent_sessions` row are resumed from their saved PydanticAI message
history. Jobs waiting for a human answer are requeued as `CLASSIFIED` after the
answer is submitted.

## Inspect the database directly

```bash
sqlite3 data/emails.db ".tables"
sqlite3 data/emails.db "SELECT re.email_id, qj.status FROM retrieved_email re JOIN queued_jobs qj ON qj.email_id=re.id WHERE re.email_id BETWEEN 90000 AND 90999 ORDER BY re.email_id;"
```

## Dashboard

```bash
uv run uvicorn api.main:app --reload --port 8000
# Dashboard: http://localhost:8000/
# Swagger:   http://localhost:8000/docs
```

The "Run Workflow" button in the dashboard is equivalent to running
`agents_workflow.workflow` from the browser. "Retrieve Emails" runs
`email_retriever.retriever` and then seeds the mock leads when the reserved
mock range is empty. It is safe to click again because both retrieval and
seeding are idempotent.

The React frontend lives in `frontend/`. Run it separately with:

```bash
cd frontend
npm run dev
```

## Slidev presentation (`Friday Afternoon/`)

```bash
cd "Friday Afternoon"
corepack pnpm install                                           # install deps (once)
corepack pnpm run dev                                            # live preview at http://localhost:3030 — highest fidelity (animations/mermaid all work)
corepack pnpm run build                                          # syntax/build check only, produces nothing presentable
corepack pnpm exec slidev export --format pptx --output <name>   # export an image-based pptx
corepack pnpm exec slidev export --format png --output <dir>     # export one PNG per slide, for your own preview/QA
```

Switch theme: change the `theme:` line in `slides.md`'s frontmatter
(`default` / `seriph` / `apple-basic`).

## If Node disappears after this machine restarts/rebuilds (common on GitHub Codespaces)

```bash
export PATH="$HOME/homebrew/bin:$PATH"
brew install node                              # builds from source, no bottle for this prefix — 10-30 min
npm install -g pnpm
```
