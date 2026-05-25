import json
from pathlib import Path

from backend.app.main import run_simulation
from backend.app.ml.risk_calibrator import build_features_from_simulation_result


PORTFOLIOS = [
    "ai_growth_sample",
    "balanced_tech_sample",
    "semiconductor_sample",
]

SCENARIOS = [
    "ai_capex_slowdown",
    "higher_for_longer_rates",
    "cloud_growth_deceleration",
    "semiconductor_export_restriction",
    "consumer_demand_weakness",
]


def score_to_level(score: int) -> str:
    if score >= 80:
        return "severe"
    if score >= 60:
        return "high"
    if score >= 35:
        return "moderate"
    return "low"


def create_variants(base_row: dict) -> list[dict]:
    variants = []
    multipliers = [
        {"name": "base", "vol": 1.0, "corr": 1.0, "hidden": 1.0, "score_delta": 0},
        {"name": "low_stress", "vol": 0.55, "corr": 0.55, "hidden": 0.65, "score_delta": -28},
        {"name": "moderate_stress", "vol": 0.90, "corr": 0.90, "hidden": 0.95, "score_delta": -6},
        {"name": "high_stress", "vol": 1.35, "corr": 1.25, "hidden": 1.15, "score_delta": 14},
        {"name": "severe_stress", "vol": 1.65, "corr": 1.40, "hidden": 1.25, "score_delta": 22},
    ]

    for item in multipliers:
        row = dict(base_row)
        row["variant"] = item["name"]
        row["portfolio_volatility"] = round(row["portfolio_volatility"] * item["vol"], 4)
        row["average_pairwise_correlation"] = round(
            min(1.0, row["average_pairwise_correlation"] * item["corr"]),
            4,
        )
        row["hidden_concentration_score"] = round(
            min(100, row["hidden_concentration_score"] * item["hidden"]),
            4,
        )

        target_score = int(max(0, min(100, row["target_score"] + item["score_delta"])))
        row["target_score"] = target_score
        row["target_level"] = score_to_level(target_score)
        row["target_level_id"] = {
            "low": 0,
            "moderate": 1,
            "high": 2,
            "severe": 3,
        }[row["target_level"]]
        row["severe_label"] = 1 if target_score >= 80 else 0

        variants.append(row)

    return variants


def main():
    rows = []

    for portfolio_id in PORTFOLIOS:
        for scenario_id in SCENARIOS:
            result = run_simulation(
                portfolio_id=portfolio_id,
                scenario_id=scenario_id,
                use_market_data=True,
            )

            features = build_features_from_simulation_result(result)

            base_row = {
                **features,
                "target_score": int(result.vulnerability_score),
                "target_level": result.risk_level,
                "target_level_id": {
                    "low": 0,
                    "moderate": 1,
                    "high": 2,
                    "severe": 3,
                }[result.risk_level],
                "severe_label": 1 if result.vulnerability_score >= 80 else 0,
                "portfolio_id": portfolio_id,
                "scenario_id": scenario_id,
                "portfolio_name": result.portfolio_name,
                "scenario_name": result.scenario.name,
            }

            rows.extend(create_variants(base_row))

    output_path = Path("datasets/risk/risk_calibration_training_data.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")

    print("\nRiskLens Alpha Risk Calibration Dataset")
    print("=" * 56)
    print(f"Rows: {len(rows)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
