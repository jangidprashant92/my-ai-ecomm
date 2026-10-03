# 15 — Scripts and Commands

## Infrastructure

```bash
docker compose up -d
docker compose ps
docker compose down
```

Destructive local reset:

```bash
docker compose down -v
```

## Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

## PostgreSQL migrations

```bash
uv run alembic current
uv run alembic history
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic downgrade -1
```

## Olist data

```bash
uv run python -m app.scripts.load_olist_data
```

This loads CSV data into PostgreSQL.

## RAG ingestion

```bash
uv run python -m app.scripts.ingest_documents
```

## RAG probes

```bash
uv run python -m app.scripts.test_embeddings
uv run python -m app.scripts.test_retrieval
uv run python -m app.scripts.test_rag
```

## Other probes

```bash
uv run python -m app.scripts.test_analytics
uv run python -m app.scripts.test_authorization
uv run python -m app.scripts.test_retry
```

## Evaluation

```bash
uv run python -m evaluation.rag.run
```

For the stable local evaluation setup used during development:

```bash
MLFLOW_GENAI_EVAL_MAX_WORKERS=1 \
MLFLOW_GENAI_EVAL_MAX_SCORER_WORKERS=1 \
uv run python -m evaluation.rag.run
```

The single-worker configuration was used to avoid the async event-loop issue encountered earlier during LLM judge execution.

## Docker logs

```bash
docker compose logs -f postgres
docker compose logs -f qdrant
```

## PostgreSQL shell

```bash
docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

## Persistence

- PostgreSQL → `postgres_data`
- Qdrant → `qdrant_storage`
- LangGraph → SQLite checkpoint file
- MLflow → configured tracking backend
