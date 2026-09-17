# Agent Workflow

The current agent workflow code is under:

```text
agents_workflow/
```

`agents_workflow/workflow.py` reads pending `QueuedJob` records from the
database and processes them one at a time.

The agent files currently define the planned boundaries:

```text
    classifier.py
    extractor_agent.py
product_catalog_research_agent.py
external_research_agent.py
email_draft_agent.py
```

The classifier and extractor use PydanticAI with typed Pydantic output models.
The remaining agents are scaffolds and will be implemented incrementally.

## Planned Flow

```text
QueuedJob
    -> classifier
    -> extractor for quotation requests
    -> product catalogue lookup
    -> external research when required
    -> quotation draft
    -> human review
```

Classification and extraction results are stored in `queued_jobs.meta_data`,
and job status advances from `PENDING` to `CLASSIFIED`, `EXTRACTED`, or
`COMPLETED`. Product lookup, retries, review, and delivery are still planned.
