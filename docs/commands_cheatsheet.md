# Command Cheatsheet

Every command you'll actually need for this project, grouped by scenario.
Unless noted otherwise, run these from the repo root (`Friday_Afternoon/`).

## Environment setup

```bash
uv sync                          # install Python dependencies
uv run alembic upgrade head       # create/upgrade the database schema
uv run alembic current            # check current schema revision
```

## Seed the 12-lead demo set and run the pipeline

```bash
uv run python -m scripts.seed_mock_leads            # seed (idempotent — reruns skip already-seeded leads)
uv run python -m scripts.seed_mock_leads --reset     # delete the previous 90000-90999 seed range, then reseed
uv run python -m agents_workflow.workflow            # run the full 5-stage pipeline (classify -> extract -> internal/external research -> draft)
```

If a run gets interrupted (e.g. a shell timeout), just run
`agents_workflow.workflow` again — each stage only picks up jobs still
sitting in that stage's status, so it safely resumes instead of
reprocessing already-finished leads.

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
`email_retriever.retriever` (fetches real IMAP mail — not needed for the
mock demo).

## Slidev presentation (`comments/Friday Afternoon/`)

```bash
cd "Friday_Afternoon/comments/Friday Afternoon"
pnpm install                                                   # install deps (once)
pnpm dev                                                        # live preview at http://localhost:3030 — highest fidelity (animations/mermaid all work)
pnpm run build                                                  # syntax/build check only, produces nothing presentable
pnpm exec slidev export --format pptx --output <name>           # export an image-based pptx
pnpm exec slidev export --format png --output <dir>             # export one PNG per slide, for your own preview/QA
```

Switch theme: change the `theme:` line in `slides.md`'s frontmatter
(`default` / `seriph` / `apple-basic`).

## If Node disappears after this machine restarts/rebuilds (common on GitHub Codespaces)

```bash
export PATH="$HOME/homebrew/bin:$PATH"
brew install node                              # builds from source, no bottle for this prefix — 10-30 min
npm install -g pnpm
```