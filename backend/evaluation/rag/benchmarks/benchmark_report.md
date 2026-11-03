# RAG Retrieval Benchmark

| Metric | baseline | mmr | hybrid |
|---|---|---|---|
| source_recall | 1.000 | 1.000 | 1.000 |
| source_precision | 1.000 | 1.000 | 1.000 |
| source_diversity | 1.000 | 1.000 | 1.000 |
| duplicate_chunk_ratio | 0.000 | 0.000 | 0.000 |
| correctness | 1.000 | 1.000 | 1.000 |
| groundedness | 1.000 | 1.000 | 1.000 |
| sufficiency | 1.000 | 1.000 | 1.000 |
| rag_quality | 1.000 | 1.000 | 1.000 |
| relevance_precision | 0.900 | 0.900 | 0.900 |
| abstention | 1.000 | 1.000 | 1.000 |
| latency_p50_ms | 3704 | 3566 | 3829 |
| latency_p95_ms | 4827 | 4650 | 8266 |

## Gate results

- **baseline**: reference
- **mmr**: PASS
- **hybrid**: FAIL — latency_p95: 8266ms > 1.5x baseline 4827ms

## Selected strategy: `baseline`

Note: the dataset has few cases, so small differences are noise. Ties go to the baseline.