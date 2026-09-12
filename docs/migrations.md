# Migrations

Alembic owns the database schema.

## Apply Migrations

```bash
uv run alembic upgrade head
```

## Check Current Revision

```bash
uv run alembic current
```

## Create a Migration

After changing a SQLAlchemy model:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

Review the generated file in:

```text
migrations/versions/
```

Then apply it:

```bash
uv run alembic upgrade head
```

## Roll Back

Roll back one revision:

```bash
uv run alembic downgrade -1
```

Roll back to the beginning:

```bash
uv run alembic downgrade base
```

## How Alembic Finds Models

`migrations/env.py` imports:

```python
from db_contexts.base import Base
from db_contexts import models
```

The model package imports every model class. This ensures all tables are
registered in:

```python
Base.metadata
```

Alembic compares that metadata with the current database and generates schema
changes.

The application should not use `Base.metadata.create_all()` for normal schema
updates. Use versioned migrations instead.
