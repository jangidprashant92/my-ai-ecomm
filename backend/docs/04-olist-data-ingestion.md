# 04 — Olist Data Ingestion

Source:

```text
datasets/raw/
```

Loader:

```text
backend/app/scripts/load_olist_data.py
```

Generic helper:

```text
backend/app/scripts/ingest.py
```

## Current datasets

1. category translation
2. products
3. customers
4. sellers
5. geolocation
6. orders
7. order items
8. payments
9. reviews

## Flow

```text
CSV
 ↓
pandas.read_csv(chunksize=5000)
 ↓
datetime conversion
 ↓
NaN → None
 ↓
records
 ↓
bulk insert
 ↓
PostgreSQL
```

Run:

```bash
cd backend
uv run python -m app.scripts.load_olist_data
```

## Important

The current loader does not implement an upsert/deduplication strategy. Re-running against an already populated database can hit primary-key constraints.

This is therefore a data-load script, not a generic migration mechanism.
