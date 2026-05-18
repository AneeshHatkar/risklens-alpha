import json
from pathlib import Path

from backend.app.services.evaluation_runner import run_evaluation_suite


def main():
    result = run_evaluation_suite(use_market_data=False)

    output_path = Path("reports/json/evaluation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\nRiskLens Alpha Evaluation Suite")
    print("=" * 48)
    print(f"Cases: {result['case_count']}")
    print(f"Passed cases: {result['passed_cases']}")
    print(f"Overall score: {result['overall_score']}/100")
    print(f"Passed: {result['passed']}")

    if result["failed_cases"]:
        print("Failed cases:", ", ".join(result["failed_cases"]))

    print(f"\nSaved evaluation results to: {output_path}")


if __name__ == "__main__":
    main()
