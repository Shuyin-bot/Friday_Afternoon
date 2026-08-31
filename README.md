# Quotation Agent

Quotation Agent is an agentic workflow for monitoring business email, identifying quotation requests, gathering trusted product information, and preparing a quotation response for human approval.

The system is designed to reduce repetitive quotation work without giving an AI agent unrestricted control over external communications or business systems.

> **Project status:** Early design and development

## Problem

Quotation requests often arrive through shared inboxes and require people to:

- Identify which messages are genuine quotation requests.
- Extract products, quantities, delivery requirements, and customer details.
- Check product, pricing, inventory, and commercial policy information.
- Prepare a consistent quotation and email response.
- Review the result before sending it to the customer.

Quotation Agent aims to automate the repetitive parts of this process while keeping important decisions and outbound communication under human control.

## Goals

- Monitor email for new messages.
- Classify whether an email is a quotation request.
- Extract structured quotation requirements from the message and attachments.
- Evaluate sender and request authenticity using technical and business signals.
- Protect the agent and connected systems from prompt injection.
- Retrieve trusted product and business data through RAG and/or MCP tools.
- Generate a proposed quotation and draft reply.
- Require human review and explicit approval before sending an email.
- Maintain an audit trail for agent decisions, tool calls, data sources, and approvals.

## Non-Goals

- Automatically sending quotations without human approval in the initial version.
- Treating an LLM's opinion as proof that a sender is authentic.
- Allowing customer-provided text to define system instructions or tool permissions.
- Using unverified information as the source of prices, stock levels, discounts, or delivery commitments.

## Core Workflow

```text
Incoming email
      |
      v
Email ingestion and normalization
      |
      v
Quotation-request classification
      |
      +---- Not a quotation request --> Route or archive
      |
      v
Sender and request verification
      |
      v
Security and prompt-injection checks
      |
      v
Requirement extraction
      |
      v
Trusted product and business data retrieval
      |       (RAG and/or MCP tools)
      v
Quote calculation and validation
      |
      v
Quotation and email draft generation
      |
      v
Human review and approval
      |
      +---- Rejected or edited --> Revise, request information, or close
      |
      v
Send approved email and record outcome
```

## Proposed Architecture

### 1. Email Ingestion

The ingestion service monitors a configured mailbox and converts messages into a normalized internal representation containing:

- Sender and recipient metadata.
- Subject and body.
- Attachments and extracted text.
- Message identifiers and timestamps.
- Email authentication results when provided by the email provider.

The original message should be preserved for traceability, while the agent receives a clearly marked, untrusted representation of its contents.

### 2. Quotation Classifier

An agent or classifier determines whether the message is related to a quotation request. It should return a structured result such as:

```json
{
  "is_quotation_request": true,
  "confidence": 0.94,
  "reason": "The sender requests pricing and availability for three products",
  "requires_human_review": false
}
```

Low-confidence messages should be routed to a review queue rather than being silently discarded.

### 3. Authenticity and Trust Evaluation

Authenticity is evaluated using multiple layers rather than relying on the LLM alone:

- SPF, DKIM, and DMARC results where available.
- Sender domain and address checks.
- Known-customer or approved-domain records.
- Conversation history and reply-to consistency.
- Suspicious attachment and link checks.
- Business rules for high-value or unusual requests.
- Human escalation when signals conflict.

These checks help estimate whether a request is trustworthy, but they do not guarantee that the sender or request is legitimate.

### 4. Security and Prompt-Injection Guardrails

All email content, attachments, retrieved documents, and external tool responses are untrusted data. They must not be treated as instructions by default.

The system should:

- Keep system instructions and customer content in separate trust boundaries.
- Prevent email text from changing tool permissions, policies, or workflow state.
- Validate tool arguments against schemas and business rules.
- Use allowlists for available tools and destinations.
- Apply least-privilege credentials to every integration.
- Require confirmation for high-impact actions.
- Scan attachments and avoid executing customer-provided code or files.
- Detect common prompt-injection patterns and route suspicious messages for review.
- Record the relevant input, decision, and action for later investigation.

Security checks should be treated as defense in depth. Prompt-injection detection is useful, but it is not a substitute for permission boundaries and human approval.

### 5. Requirement Extraction

The agent converts the request into structured fields that can be validated before a quote is generated:

- Customer name and contact details.
- Product names, identifiers, quantities, and units.
- Required delivery location and date.
- Currency and tax requirements.
- Requested discounts or commercial terms.
- Missing or ambiguous information.

The agent should ask for clarification or flag missing fields instead of guessing.

### 6. Product Data Retrieval

Product and business information can be retrieved using a retrieval-augmented generation layer, MCP servers, or both. Potential data sources include:

- Product catalogues.
- Current price lists.
- Inventory systems.
- Customer-specific pricing.
- Discount and approval policies.
- Delivery and tax rules.
- Previous approved quotations.

Every important value in a quotation should be traceable to a trusted source and timestamp. The model should not invent a price, product specification, stock level, or delivery promise.

### 7. Quote Calculation and Validation

Deterministic application code should perform calculations such as:

- Line totals.
- Discounts.
- Taxes.
- Shipping and other fees.
- Currency conversions, where supported.
- Grand totals.

The LLM may explain or format a quotation, but it should not be the source of truth for arithmetic or commercial rules.

### 8. Draft Generation and Human Review

The system produces:

- A structured quotation.
- A customer-facing email draft.
- The data sources used.
- Assumptions and unresolved issues.
- A risk or confidence summary.

The draft is placed in a human review queue. A reviewer must be able to inspect, edit, approve, reject, or request clarification. Only an explicit approval may trigger the outbound email action.

## Example

### Incoming request

```text
Subject: Request for quotation - network equipment

Hello,

Please provide pricing and availability for:

- 10 x Model A routers
- 5 x Model B switches

Please include delivery to Accra and indicate the expected delivery date.
```

### Internal result

```text
Classification: Quotation request
Sender status: Requires verification
Missing information: Customer billing details
Retrieved data: Current catalogue and price list
Risk flags: None detected
Action: Draft quotation and route to human review
```

The agent should not send a response until the sender has passed the configured checks and a reviewer approves the final draft.

## Human-in-the-Loop Policy

Human approval is required before:

- Sending an external email.
- Confirming a price, discount, stock level, or delivery commitment.
- Sharing sensitive customer or company information.
- Accepting unusual commercial terms.
- Proceeding when authenticity or security checks fail.

The approval record should include the reviewer, timestamp, version of the draft, and any edits made before approval.

## Observability and Auditability

Each request should have a correlation ID and an auditable lifecycle. Logs should capture:

- Message and attachment identifiers.
- Classification and extraction results.
- Authenticity and security signals.
- Retrieved documents or tool responses.
- Tool calls and validated arguments.
- Quote calculation inputs and outputs.
- Generated draft versions.
- Reviewer actions and final delivery status.

Logs must avoid exposing secrets and should follow the project's data-retention and privacy requirements.

## Initial Roadmap

1. Define the normalized email and quotation schemas.
2. Integrate with an email provider in read-only mode.
3. Add quotation-request classification and confidence thresholds.
4. Extract products, quantities, and missing requirements.
5. Add sender verification and security guardrails.
6. Connect a trusted product catalogue through RAG or MCP.
7. Implement deterministic quote calculation and validation.
8. Generate quotation and email drafts.
9. Build a human review and approval workflow.
10. Add approved outbound email sending.
11. Add evaluation datasets, monitoring, and additional communication channels.

## Evaluation Criteria

The project should be evaluated on more than response quality:

- Correct quotation-request classification.
- Accurate extraction of products, quantities, and customer requirements.
- Correct use of current and authorized product data.
- Correct deterministic calculations.
- Resistance to prompt injection and malicious attachments.
- Appropriate handling of suspicious or ambiguous senders.
- No unauthorized tool calls or outbound messages.
- Human approval enforcement.
- Complete and useful audit records.
- Clear escalation when information is missing or confidence is low.

## Development

The implementation stack and local setup instructions will be added as the project is built. Planned configuration areas include:

- Email provider credentials and mailbox settings.
- LLM provider and model configuration.
- RAG storage or vector database configuration.
- MCP server endpoints and permissions.
- Product, pricing, inventory, and policy data sources.
- Human review application settings.
- Logging, monitoring, and data-retention settings.

Never commit credentials, API keys, customer emails, or production data to the repository.

## License

License information will be added when the project license is selected.
