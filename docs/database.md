# Database

## Connection and Sessions

Database configuration is in:

```text
db_contexts/sessions.py
```

It creates:

```text
DATABASE_URL
engine
SessionLocal
```

The database URL can be supplied through `EMAIL_DB_URL`. If it is absent, the
application builds a SQLite URL from `EMAIL_DB_PATH`, defaulting to:

```text
sqlite:///data/emails.db
```

Models use the shared declarative base in:

```text
db_contexts/base.py
```

## Email Tables

`retrieved_email` stores email metadata:

```text
id
email_id
from_email
subject
created_at
```

`email_id` is unique and represents the external IMAP message identifier.

`queued_jobs` stores work associated with an email:

```text
id
status
email_id
meta_data
created_at
```

`queued_jobs.email_id` is a foreign key to `retrieved_email.id`, which is the
internal database primary key. The repository creates the email, flushes the
session to obtain its generated `id`, and then creates the queue row with that
ID.

## Packaging Tables

`products` stores the company's catalogue. It includes SKU, product name,
packaging category, box style, material, dimensions, unit of measure, and
active status.

`product_aliases` stores alternate terms such as:

```text
small kraft mailer
shipping box
pizza carton
```

`warehouses` stores physical locations. `inventory` connects products to
warehouses and records on-hand, reserved, and reorder quantities.

`price_lists` identifies a currency-specific list. `product_prices` stores
quantity breaks and validity windows for product prices.

## Repository Functions

Product access is in:

```text
db_contexts/repos/product_repository.py
```

The current functions are:

```text
create_product
find_exact_product
list_products
get_inventory
get_current_price
```

These functions create short-lived SQLAlchemy sessions and return ORM objects.
They should be called by application services or future tools rather than by
the email retriever directly.
