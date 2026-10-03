# 17 — Current Status and Roadmap

## Completed

- LangGraph root graph
- intent classification
- CommerceAgent
- tools
- database workflow
- temporal resolution
- authorization
- HITL
- checkpointing
- SSE
- MLflow tracing
- Markdown knowledge base
- chunking
- embeddings
- Qdrant retrieval
- query rewriting
- reranking
- minimal context
- grounded answer
- RAG evaluation
- abstention evaluation

## Current evaluation status

The latest uploaded 12-row CSV is a good baseline.

Important findings:

1. Source recall is 1.0.
2. Source precision is 0.5 only for the first row because the retrieved SOP duplicates information from the canonical refund policy.
3. The cross-policy question is factually correct but the retrieval-relevance judge gives 0.0 precision; this should be treated as a judge disagreement to investigate, not an automatic retrieval failure.
4. Both negative questions correctly abstain.
5. The two procedural questions are correctly answered according to the custom RAG-quality judge, while generic correctness says `no` because the expected-facts assessment is incomplete.

## Before the next feature

Stabilize the benchmark:

```text
correct required_sources
        ↓
complete expected_facts
        ↓
add genuine multi-source cases
        ↓
add paraphrase/follow-up cases
        ↓
rerun
        ↓
freeze baseline
```

## Next engineering stages

```text
stable RAG baseline
    ↓
MMR / diversity-aware retrieval
    ↓
hybrid retrieval
    ↓
agentic RAG
    ↓
memory
    ↓
MCP
    ↓
deeper agent orchestration
    ↓
production evaluation / CI
```

Do not implement multiple retrieval changes at once. One change per experiment makes the evaluation scientifically useful.
