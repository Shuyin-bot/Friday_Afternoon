# Agent Workflow

The current agent workflow code is under:

```text
agents_workflow/
```

`agents_workflow/workflow.py` currently reads pending `QueuedJob` records from
the database and prints them. It is the starting point for the worker that
will process queued quotation requests.

The agent files currently define the planned boundaries:

```text
classifier_extractor_agent.py
product_catalog_research_agent.py
external_research_agent.py
email_draft_agent.py
```

These agents are scaffolds at the moment. They are intended to be implemented
incrementally with Pydantic/PydanticAI and will eventually classify email,
extract quotation requirements, query product data, perform external research,
and generate drafts.

## Planned Flow

```text
QueuedJob
    -> classifier and extractor
    -> product catalogue lookup
    -> external research when required
    -> quotation draft
    -> human review
```

The database and email retriever are currently usable independently of this
workflow scaffold, which allows each agent to be developed and tested in
isolation.
