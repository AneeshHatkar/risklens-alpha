from backend.app.services.evaluation_runner import (
    evaluate_no_advice_safety,
    load_evaluation_cases,
    run_evaluation_suite,
    score_overlap,
)
from backend.app.main import run_simulation


def test_score_overlap():
    actual = ["AI infrastructure", "semiconductors", "cloud growth"]
    expected = ["AI infrastructure", "cloud growth"]

    assert score_overlap(actual, expected) == 1.0


def test_load_evaluation_cases():
    cases = load_evaluation_cases()

    assert len(cases) >= 3
    assert "case_id" in cases[0]
    assert "portfolio_id" in cases[0]
    assert "scenario_id" in cases[0]


def test_no_advice_safety_passes_for_simulation():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    safety = evaluate_no_advice_safety(result)

    assert safety["passed"] is True
    assert safety["score"] == 100


def test_run_evaluation_suite_returns_scores():
    result = run_evaluation_suite(use_market_data=False)

    assert result["case_count"] >= 3
    assert 0 <= result["overall_score"] <= 100
    assert "results" in result
    assert "failed_cases" in result
