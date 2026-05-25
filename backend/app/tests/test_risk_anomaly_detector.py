from backend.app.ml.risk_anomaly_detector import (
    detect_risk_timeline_anomalies,
    detect_series_anomalies,
    safe_z_score,
)


def sample_points():
    return [
        {
            "id": 1,
            "portfolio_id": 1,
            "scenario_id": "s1",
            "scenario_name": "Scenario 1",
            "vulnerability_score": 60,
            "risk_level": "high",
            "hidden_concentration_score": 70,
            "confidence_lower": 54,
            "confidence_upper": 66,
            "source": "test",
            "created_at": "2026-05-01T10:00:00",
        },
        {
            "id": 2,
            "portfolio_id": 1,
            "scenario_id": "s1",
            "scenario_name": "Scenario 1",
            "vulnerability_score": 62,
            "risk_level": "high",
            "hidden_concentration_score": 71,
            "confidence_lower": 55,
            "confidence_upper": 67,
            "source": "test",
            "created_at": "2026-05-02T10:00:00",
        },
        {
            "id": 3,
            "portfolio_id": 1,
            "scenario_id": "s1",
            "scenario_name": "Scenario 1",
            "vulnerability_score": 61,
            "risk_level": "high",
            "hidden_concentration_score": 72,
            "confidence_lower": 55,
            "confidence_upper": 68,
            "source": "test",
            "created_at": "2026-05-03T10:00:00",
        },
        {
            "id": 4,
            "portfolio_id": 1,
            "scenario_id": "s1",
            "scenario_name": "Scenario 1",
            "vulnerability_score": 88,
            "risk_level": "severe",
            "hidden_concentration_score": 92,
            "confidence_lower": 68,
            "confidence_upper": 100,
            "source": "test",
            "created_at": "2026-05-04T10:00:00",
        },
    ]


def test_safe_z_score_returns_number():
    z_score = safe_z_score(90, [60, 62, 61])

    assert z_score > 0


def test_detect_series_anomalies_finds_spike():
    anomalies = detect_series_anomalies(
        points=sample_points(),
        field="vulnerability_score",
        min_history=3,
        z_threshold=1.5,
    )

    assert len(anomalies) >= 1
    assert anomalies[0]["field"] == "vulnerability_score"


def test_detect_risk_timeline_anomalies_shape():
    result = detect_risk_timeline_anomalies(sample_points())

    assert result["point_count"] == 4
    assert result["anomaly_count"] >= 1
    assert "summary" in result
    assert "anomalies" in result
