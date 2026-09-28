# Quotation Bot Frontend

React dashboard for monitoring quotation jobs and reviewing AI-generated
quotation drafts.

## Features

- View job statistics and workflow statuses
- Browse and inspect quotation jobs
- Review original emails, research details, and quotation drafts
- Approve, edit, reject, or comment on drafts
- Answer human-input requests
- Receive live updates through Server-Sent Events

## Tech Stack

- React
- Vite
- Material UI
- Emotion
- JavaScript

## Setup

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend normally runs at:

```text
http://localhost:5173
```

The Vite development server proxies `/api` requests to the FastAPI backend at
`http://localhost:8000`.

Start the backend from the main project directory:

```bash
uv run uvicorn api.main:app --reload --port 8000
```

## Other Commands

```bash
npm run build    # Create a production build
npm run preview  # Preview the production build
npm run lint     # Run Oxlint
```
