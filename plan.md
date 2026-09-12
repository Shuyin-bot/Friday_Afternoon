# Quotation Bot Plan

## Current Scope

The current project is the database-backed email-ingestion foundation for an
agentic quotation assistant. It currently retrieves emails from IMAP, stores
email metadata, creates queued work, and defines the product data needed by a
packaging manufacturer. The agent implementations are intentionally being
built incrementally with Pydantic/PydanticAI.

## Current Flow

```text
IMAP mailbox
    -> email_retriever
    -> RetrievedEmail metadata
    -> QueuedJob with PENDING status
    -> email JSON artifact
```

Database schema changes are managed with SQLAlchemy models and Alembic
migrations.

## Implemented

### Email retrieval

- Connect to an IMAP mailbox.
- Search all or unseen messages.
- Skip email IDs already recorded.
- Fetch and parse plain-text content.
- Store email metadata in SQLite.
- Create a pending queue job.
- Write the retrieved email to a JSON artifact.

### Database foundation

- Shared SQLAlchemy declarative base.
- SQLAlchemy session factory.
- Email and queued-job models.
- Repository functions for email deduplication.
- Alembic migration configuration.
- Initial email and queue migration.

### Packaging catalogue

- Products and SKUs.
- Product aliases.
- Packaging categories.
- Box styles, materials, and dimensions.
- Warehouses.
- Inventory by warehouse.
- Currency-specific price lists.
- Quantity-based and date-valid product prices.
- Repository functions for product, inventory, and price queries.

## Next Steps

### Queue processing

- Add a worker that consumes `QueuedJob` records.
- Add explicit job transitions and retry handling.
- Record processing errors without losing the original email.

### Product resolution

- Use exact SKU, name, and alias lookup first.
- Add semantic product search as a fallback.
- Return candidates and confidence rather than inventing products.

### Quotation extraction

- Define typed quotation-request models.
- Extract products, quantities, delivery requirements, and missing fields.
- Keep email content outside the trusted system-instruction boundary.

### Agent integration

- Add focused PydanticAI agents.
- Keep database access inside explicit Python tools.
- Validate all agent inputs and outputs.
- Require human review before external communication.

### Review and delivery

- Persist quotation drafts.
- Add review, approval, rejection, and revision states.
- Add outbound email only after approval controls are complete.
