# Developer Documentation

This directory explains how the Quotation Agent is organized and how to operate and maintain it.

## Start Here

1. Read [Getting Started](getting-started.md) to install dependencies and run the tests.
2. Read [Architecture](architecture.md) to understand how an email moves through the system.
3. Read [Maintenance Guide](maintenance.md) before changing a layer or adding an integration.

## Current Implementation

The implemented proof of concept currently supports:

```text
IMAP email detection
  -> email retrieval and normalization
  -> SQLite ingestion state
  -> raw and normalized artifacts
  -> SQLite job queue
  -> manually configured Python agent worker
```

The system does not yet include Ollama calls, real PydanticAI agents, a complete multi-agent workflow, RAG, MCP, a review UI, or outbound email sending.
