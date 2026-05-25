from backend.app.ml.risk_anomaly_detector import detect_risk_timeline_anomalies


def main():
    sample_points = [
        {
            "id": 1,
            "portfolio_id": 1,
            "scenario_id": "ai_capex_slowdown",
            "scenario_name": "AI Infrastructure Spending Slowdown",
            "vulnerability_score": 61,
            "risk_level": "high",
            "hidden_concentration_score": 72,
            "confidence_lower": 55,
            "confidence_upper": 67,
            "source": "test",
            "created_at": "2026-05-01T10:00:00",
        },
        {
            "id": 2,
            "portfolio_id": 1,
            "scenario_id": "ai_capex_slowdown",
            "scenario_name": "AI Infrastructure Spending Slowdown",
            "vulnerability_score": 63,
            "risk_level": "high",
            "hidden_concentration_score": 73,
            "confidence_lower": 57,
            "confidence_upper": 69,
            "source": "test",
            "created_at": "2026-05-02T10:00:00",
        },
        {
            "id": 3,
            "portfolio_id": 1,
            "scenario_id": "ai_capex_slowdown",
            "scenario_name": "AI Infrastructure Spending Slowdown",
            "vulnerability_score": 62,
            "risk_level": "high",
            "hidden_concentration_score": 74,
            "confidence_lower": 56,
            "confidence_upper": 68,
            "source": "test",
            "created_at": "2026-05-03T10:00:00",
        },
        {
            "id": 4,
            "portfolio_id": 1,
            "scenario_id": "ai_capex_slowdown",
            "scenario_name": "AI Infrastructure Spending Slowdown",
            "vulnerability_score": 86,
            "risk_level": "severe",
            "hidden_concentration_score": 91,
            "confidence_lower": 70,
            "confidence_upper": 98,
            "source": "test",
            "created_at": "2026-05-04T10:00:00",
        },
    ]

    result = detect_risk_timeline_anomalies(sample_points)

    print("\nRiskLens Alpha Timeline Anomaly Detection")
    print("=" * 56)
    print(f"Timeline points: {result['point_count']}")
    print(f"Anomalies: {result['anomaly_count']}")
    print(f"High: {result['high_count']}")
    print(f"Medium: {result['medium_count']}")
    print(f"Summary: {result['summary']}")

    print("\nAnomalies:")
    for anomaly in result["anomalies"]:
        print(f"- [{anomaly['severity'].upper()}] {anomaly['message']}")


if __name__ == "__main__":
    main()
