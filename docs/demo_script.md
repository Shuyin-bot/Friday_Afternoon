# MVP Demo Script

Prep and talking-track for the 2-day MVP demo. Covers the seeded mock lead
set (`scripts/seed_mock_leads.py`), what each lead is meant to show, and the
known gaps to state proactively rather than let the audience discover.

## Before you present

1. **Add a real `TAVILY_API_KEY` to `.env`.** It is currently empty, so every
   external company research step is skipped end to end — the "the agent
   researched who's writing to us" moment will not work at all without a
   real key. This is the single most important pre-demo checklist item.
2. Reset and reseed the demo leads so the run is fresh and reproducible:
   ```bash
   uv run python -m scripts.seed_mock_leads --reset
   ```
3. Run the full pipeline once before presenting, so you already know what
   each stage produced and are not debugging live:
   ```bash
   uv run python -m agents_workflow.workflow
   ```
4. Start the dashboard:
   ```bash
   uv run uvicorn api.main:app --reload --port 8000
   ```
   Seeded demo leads are prefixed `[MOCK LEAD-2026-...]` in the subject line
   and use `.example` sender domains, so they are easy to pick out from any
   real test-mailbox traffic also sitting in the dashboard.
5. Optional, for a "watch it happen live" moment instead of pre-computed
   results: reset right before presenting and trigger `Run Workflow` from
   the dashboard UI in front of the audience instead of the CLI. Each lead
   takes several LLM calls (classify → extract → research → research →
   draft), so budget roughly 10-20s per lead, more if Tavily is slow.

## Suggested walkthrough order (pick 4-6 of these, don't run all 12 live)

| # | Lead | What to say while showing it |
|---|---|---|
| 1 | LEAD-2026-016 (Alb-Gold Teigwaren, pasta manufacturer) | The flagship case: a real two-machine request (case erector + carton sealer). Show classify → extract (both products captured as separate items, not merged into one string) → catalog research (both SKUs found by exact match) → draft (mentions both machines, correct commercial terms, signed by the right person). This is the "everything works" case. |
| 2 | LEAD-2026-038 (Tiernahrung Deuerer, pet food) | A technical question in the email ("hot-melt or tape for cold storage?"). Show that the draft answers from the catalog's `specs` field rather than guessing, and that anything requiring an engineering check is flagged as such, not promised outright. |
| 3 | LEAD-2026-025 (Mubea, automotive) | Asks specifically "can your palletizing cell handle KLT containers?" — the catalog lists this as an option that "requires an engineering check". Show the draft correctly hedges instead of over-promising. |
| 4 | LEAD-2026-027 (Felsengartenkellerei, existing customer) | An existing customer ordering a format set + wear kit by serial number. Show the extractor catching two requested items that both resolve to the same SKU (PFS-FS-KIT), and the draft adopting a warmer, relationship tone. |
| 5 | LEAD-2026-029 (phishing) | The security case. Show that classify correctly stops it at COMPLETED with `is_quote: false` — no extraction, no research, no draft, no tool calls at all. This is the "the agent never touches hostile input" guarantee. |
| 6 | LEAD-2026-018 or LEAD-2026-040 | A supplier's own sales pitch (018) or a misrouted own-supplier invoice (040). Both correctly classify as non-quotes and stop immediately — shows the agent isn't just saying yes to everything that looks like business email. |

If `TAVILY_API_KEY` is configured, add one more beat: re-run LEAD-2026-016
or -028 and show the `external_research` stage actually returning real
information about Alb-Gold Teigwaren GmbH / Athletic Brewing Company, and
the draft weaving that into a personalised opening line.

## What to say if asked "does it do X" — known, deliberate gaps

State these proactively rather than waiting to be caught:

- **No lead scoring / fit ranking.** The mock dataset includes a scoring
  rubric (A1-A5) and historical outcomes for calibration, but there is no
  Scoring agent yet. This MVP shows intake → draft only.
- **No outbound sending.** Everything you see is a draft sitting in the
  dashboard. There is no send/approve action yet — human review happens by
  reading the dashboard, not by clicking "send" in it.
- **No RAG over past correspondence or historical outcomes.** The draft
  agent is grounded in the live product catalog (SQL + Chroma semantic
  search) and the seller's company profile, both looked up directly, not
  retrieved via embeddings over past emails.
- **Company research is live-web (Tavily), not a sandboxed dataset.** That
  is why 8 of the 12 demo leads use real companies (Alb-Gold, Thise Mejeri,
  Mubea, Felsengartenkellerei, Rügenwalder Mühle, Athletic Brewing, Fiege,
  Tiernahrung Deuerer) instead of the mock dataset's fictional ones — so the
  live search actually returns something. The other 4 leads (freemail
  two-liner, supplier pitch, phishing, misrouted invoice) keep their
  original fictional/no-company identity on purpose, to show graceful
  handling when there is nothing to research.

## Where this data comes from

- `mock_data/FREEZE_LOG.md` — the frozen v1 baseline (50 leads) and how the
  12-lead demo subset (`leads/email_inbox.v1-demo.json`) was derived from it.
- `mock_data/leads/email_inbox.v1-demo.json`'s own `source_mapping` field —
  which original fictional lead maps to which real company, and why.
- Ground truth for the full 50-lead baseline lives outside both repos, at
  `~/Desktop/ground_truth/`, for human comparison only. It is never read by
  any agent and never should be.
