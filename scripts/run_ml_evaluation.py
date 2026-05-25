import json
from pathlib import Path

from backend.app.services.ml_evaluation import run_ml_evaluation_suite


def main():
    result = run_ml_evaluation_suite()

    output_path = Path("reports/json/ml_evaluation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\nRiskLens Alpha ML Evaluation Suite")
    print("=" * 56)
    print(f"Overall score: {result['overall_score']}/100")
    print(f"Passed: {result['passed']}")
    print(f"Passed checks: {result['passed_checks']}/{result['total_checks']}")

    print("\nChecks:")
    for name, check in result["checks"].items():
        print(f"- {name}: {check['status']} | passed={check['passed']}")
        print(f"  {check.get('summary', '')}")

    print(f"\nSaved ML evaluation to: {output_path}")


if __name__ == "__main__":
    main()
