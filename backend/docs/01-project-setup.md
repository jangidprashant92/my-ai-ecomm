# 01 — Project Setup

## Prerequisites

- Python 3.11+
- uv
- Docker / Docker Compose
- Node.js / npm
- configured chat model
- Azure OpenAI-compatible embeddings

## Start infrastructure

From repository root:

```bash
docker compose up -d
docker compose ps
```

## Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Important environment variables

- `DATABASE_URL`
- `MODEL_NAME`
- `LANGGRAPH_CHECKPOINT_DB`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSIONS`
- `QDRANT_URL`
- `QDRANT_COLLECTION`
- `OPENAI_API_KEY`
- `EMBEDDING_ENDPOINT`
- `EVAL_JUDGE_MODEL`

Never commit real secrets.
