import pandas as pd
import pytest
from evaluation.rag.benchmark import (
    evaluate_gates,
    select_winner,
    summarize,
    to_score,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("yes", 1.0),
        ("NO", 0.0),
        ("pass", 1.0),
        (True, 1.0),
        (0.5, 0.5),
        (None, None),
        ("junk", None),
    ],
)
def test_to_score(raw, expected):
    assert to_score(raw) == expected


def _df():
    return pd.DataFrame(
        {
            "case_id": ["a", "b", "n"],
            "case_category": ["direct", "comparison", "negative"],
            "source_recall/value": [1.0, 1.0, None],
            "source_precision/value": [1.0, 0.5, None],
            "correctness/value": ["yes", "yes", None],
            "retrieval_groundedness/value": ["yes", "yes", None],
            "retrieval_sufficiency/value": ["yes", "no", None],
            "commerceops_rag_quality/value": ["pass", "pass", None],
            "abstention_quality/value": [None, None, "pass"],
        }
    )


def test_summarize_splits_answerable_and_negative():
    s = summarize(_df(), [100.0, 200.0, 300.0])
    assert s["n_answerable"] == 2 and s["n_negative"] == 1
    assert s["source_precision"] == 0.75
    assert s["sufficiency"] == 0.5
    assert s["abstention"] == 1.0
    assert s["latency_p50_ms"] == 200.0


def test_summarize_requires_category():
    with pytest.raises(ValueError):
        summarize(_df().drop(columns=["case_category"]), [])


def _good(**over):
    base = {
        "source_recall": 1.0,
        "correctness": 1.0,
        "groundedness": 1.0,
        "sufficiency": 1.0,
        "rag_quality": 1.0,
        "abstention": 1.0,
        "source_precision": 1.0,
        "latency_p50_ms": 1000.0,
        "latency_p95_ms": 2000.0,
    }
    return {**base, **over}


def test_gates_pass_when_equal():
    assert evaluate_gates(_good(), _good()) == []


def test_gates_fail_on_regression_abstention_and_latency():
    fails = evaluate_gates(
        _good(), _good(correctness=0.8, abstention=0.5, latency_p95_ms=4000.0)
    )
    joined = " ".join(fails)
    assert (
        "correctness" in joined and "abstention" in joined and "latency_p95" in joined
    )


def test_tie_prefers_baseline():
    summaries = {"baseline": _good(), "mmr": _good(), "hybrid": _good()}
    assert select_winner(summaries, {"mmr": [], "hybrid": []}) == "baseline"


def test_failing_candidate_never_wins():
    summaries = {
        "baseline": _good(source_precision=0.8),
        "hybrid": _good(source_precision=1.0),
    }
    assert select_winner(summaries, {"hybrid": ["abstention: 0.5"]}) == "baseline"


def test_passing_better_candidate_wins():
    summaries = {
        "baseline": _good(source_precision=0.8),
        "hybrid": _good(source_precision=1.0),
    }
    assert select_winner(summaries, {"hybrid": []}) == "hybrid"
