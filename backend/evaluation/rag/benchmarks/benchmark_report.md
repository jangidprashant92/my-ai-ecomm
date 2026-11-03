# RAG Retrieval Benchmark

| Metric | baseline | mmr | hybrid |
|---|---|---|---|
| source_recall | 1.000 | 1.000 | 1.000 |
| source_precision | 1.000 | 1.000 | 1.000 |
| correctness | 1.000 | 1.000 | 1.000 |
| groundedness | 1.000 | 1.000 | 1.000 |
| sufficiency | 1.000 | 1.000 | 1.000 |
| rag_quality | 1.000 | 1.000 | 1.000 |
| relevance_precision | 0.900 | 0.900 | 0.900 |
| abstention | 1.000 | 1.000 | 1.000 |
| latency_p50_ms | 4225 | 4089 | 4554 |
| latency_p95_ms | 4878 | 4788 | 4815 |

## Gate results

- **baseline**: reference
- **mmr**: PASS
- **hybrid**: PASS

## Selected strategy: `baseline`

Note: the dataset has few cases, so small differences are noise. Ties go to the baseline.