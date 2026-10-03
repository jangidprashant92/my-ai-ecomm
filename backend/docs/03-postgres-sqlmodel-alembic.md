# 03 — PostgreSQL, SQLModel and Alembic

## Persistence distinction

The project uses:

- PostgreSQL for application/business data.
- SQLite for LangGraph checkpoints.
- Qdrant for vectors.
- MLflow for observability/evaluation.

Olist CSVs are **not** currently migrated to SQLite.

## SQLModel

Models live under `backend/app/models/`.

Examples:

- `customer.py`
- `order.py`
- `product.py`

## Database engine

`backend/app/core/database.py` creates the engine from `DATABASE_URL`.

It provides:

- `get_session()`
- `create_session()`

## Alembic

Configuration:

```text
backend/alembic.ini
backend/migrations/
```

Common commands:

```bash
uv run alembic current
uv run alembic history
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic downgrade -1
```

Recommended flow:

```text
change SQLModel
  ↓
alembic revision --autogenerate
  ↓
review migration
  ↓
alembic upgrade head
```
