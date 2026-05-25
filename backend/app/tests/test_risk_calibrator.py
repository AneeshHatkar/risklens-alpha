from backend.app.main import run_simulation
from backend.app.ml.risk_calibrator import (
    build_features_from_simulation_result,
    predict_calibrated_risk_from_features,
    train_risk_calibrator,
)


def make_small_training_dataset(dataset_path):
    import json

    rows = []
    scores = [30, 45, 62, 78, 85, 92, 55, 70, 81, 40, 65, 88, 25, 50, 75, 95]

    for score in scores:
        level = (
            "severe"
            if score >= 80
            else "high"
            if score >= 60
            else "moderate"
            if score >= 35
            else "low"
        )

        rows.append(
            {
                "scenario_severity": 0.7,
                "portfolio_volatility": score / 200,
                "average_pairwise_correlation": 0.5,
                "hidden_concentration_score": score,
                "confidence_lower": max(0, score - 5),
                "confidence_upper": min(100, score + 5),
                "confidence_width": 10,
                "agent_disagreement_score": 25,
                "factor_count": 4,
                "holding_risk_avg": score / 2,
                "holding_risk_max": score,
                "market_data_available": 1,
                "target_score": score,
                "target_level": level,
                "target_level_id": {"low": 0, "moderate": 1, "high": 2, "severe": 3}[level],
                "severe_label": 1 if score >= 80 else 0,
            }
        )

    with dataset_path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")


def test_build_features_from_simulation_result():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    features = build_features_from_simulation_result(result)

    assert "scenario_severity" in features
    assert "hidden_concentration_score" in features
    assert "agent_disagreement_score" in features


def test_train_risk_calibrator_creates_model(tmp_path):
    dataset_path = tmp_path / "risk_training.jsonl"
    model_path = tmp_path / "risk_calibrator.joblib"

    make_small_training_dataset(dataset_path)

    metrics = train_risk_calibrator(
        dataset_path=str(dataset_path),
        model_path=str(model_path),
        test_size=0.25,
    )

    assert model_path.exists()
    assert metrics["row_count"] == 16
    assert "score_model" in metrics
    assert "level_model" in metrics
    assert "severe_model" in metrics


def test_predict_calibrated_risk_from_features_after_training(tmp_path):
    dataset_path = tmp_path / "risk_training.jsonl"
    model_path = tmp_path / "risk_calibrator.joblib"

    make_small_training_dataset(dataset_path)

    train_risk_calibrator(
        dataset_path=str(dataset_path),
        model_path=str(model_path),
        test_size=0.25,
    )

    prediction = predict_calibrated_risk_from_features(
        {
            "scenario_severity": 0.8,
            "portfolio_volatility": 0.4,
            "average_pairwise_correlation": 0.7,
            "hidden_concentration_score": 85,
            "confidence_lower": 78,
            "confidence_upper": 92,
            "confidence_width": 14,
            "agent_disagreement_score": 30,
            "factor_count": 5,
            "holding_risk_avg": 42,
            "holding_risk_max": 88,
            "market_data_available": 1,
        },
        model_path=str(model_path),
    )

    assert 0 <= prediction["calibrated_score"] <= 100
    assert 0 <= prediction["severe_probability"] <= 1
    assert prediction["calibrated_level"] in {"low", "moderate", "high", "severe"}
