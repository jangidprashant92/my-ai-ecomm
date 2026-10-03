# 13 — RAG Evaluation

Location:

```text
backend/evaluation/rag/
```

Important files:

- `dataset.json`
- `predictor.py`
- `scorers.py`
- `run.py`
- `results.csv`

## Flow

```text
dataset.json
 ↓
predict_fn
 ↓
RagService.answer_sync()
 ↓
MLflow trace
 ↓
custom + LLM judges
 ↓
result_df
 ↓
results.csv
```

## Metrics

### Source recall
Were the required sources retrieved?

### Source precision
How many retrieved sources are expected/relevant according to the benchmark?

### Abstention quality
For unanswerable questions, did the system retrieve nothing relevant and explicitly abstain?

### Retrieval relevance
LLM judge evaluates document relevance.

### Groundedness
Does the answer stay supported by retrieved context?

### Sufficiency
Is retrieved context sufficient for the expected facts?

### Correctness
Does the answer satisfy expected facts?

### CommerceOps RAG quality
Custom PASS/PARTIAL/FAIL judge.

## Run

```bash
cd backend
uv run python -m evaluation.rag.run
```

## Important benchmark rule

Do not mark a document as required merely because it contains duplicate supporting information.

A required source should be necessary for the expected answer.

For negative cases, abstention is more meaningful than generic factual correctness.

## Latest uploaded 12-case result

The uploaded CSV shows:

- source recall: 1.0 for all 12
- source precision: 0.5 on the first case because two sources were retrieved while only one was treated as required; 1.0 on the remaining cases
- cross-policy retrieval relevance is currently the main MLflow retrieval-relevance disagreement
- both negative cases correctly abstain
- all 8 answerable cases produce correct answers according to the detailed expected-facts/custom quality evaluation
- two long procedural cases are marked `correctness=no` by the generic correctness judge even though the custom RAG-quality judge says PASS; its rationale is that the expected-facts assessment did not list every SOP step.

This is an evaluation alignment issue, not evidence that the RAG answer is wrong.

## Next dataset cleanup

The GitHub `dataset.json` inspected in this session still contains the older 10-case version.

Before using it as the permanent baseline:

1. remove duplicate `required_sources` from `rag-001`, `rag-007`, and `rag-008` where one canonical document is sufficient;
2. keep a genuine multi-source comparison case;
3. add the two procedural cases with complete expected facts;
4. keep the two negative cases;
5. rerun the benchmark.

Do not move to MMR/hybrid retrieval until this benchmark is stable.
