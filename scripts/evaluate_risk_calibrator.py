from backend.app.main import run_simulation
from backend.app.ml.risk_calibrator import predict_calibrated_risk_from_result


def main():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=True,
    )

    prediction = predict_calibrated_risk_from_result(result)

    print("\nRiskLens Alpha ML Risk Calibration")
    print("=" * 56)
    print(f"Portfolio: {result.portfolio_name}")
    print(f"Scenario: {result.scenario.name}")
    print(f"Base score: {prediction['base_score']}/100")
    print(f"Base level: {prediction['base_level']}")
    print(f"Calibrated score: {prediction['calibrated_score']}/100")
    print(f"Calibrated level: {prediction['calibrated_level']}")
    print(f"Severe probability: {prediction['severe_probability']}")

    print("\nFeatures used:")
    for key, value in prediction["features_used"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
