from backend.app.services.ml_evaluation import (
    evaluate_dynamic_factor_update_health,
    evaluate_narrative_classifier_status,
    evaluate_news_aware_simulation_health,
    evaluate_risk_calibrator_status,
    run_ml_evaluation_suite,
)


def test_narrative_classifier_status_shape():
    result = evaluate_narrative_classifier_status()

    assert "status" in result
    assert "passed" in result
    assert "model" in result


def test_risk_calibrator_status_shape():
    result = evaluate_risk_calibrator_status()

    assert "status" in result
    assert "passed" in result
    assert "model" in result


def test_dynamic_factor_update_health():
    result = evaluate_dynamic_factor_update_health()

    assert "status" in result
    assert "passed" in result
    assert "adjustment_count" in result


def test_news_aware_simulation_health():
    result = evaluate_news_aware_simulation_health()

    assert "status" in result
    assert "passed" in result
    assert "news_adjusted" in result


def test_run_ml_evaluation_suite():
    result = run_ml_evaluation_suite()

    assert result["suite_name"] == "RiskLens Alpha ML Evaluation Suite"
    assert 0 <= result["overall_score"] <= 100
    assert "checks" in result
