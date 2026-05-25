import json
from pathlib import Path

from backend.app.ml.risk_calibrator import train_risk_calibrator


def main():
    metrics = train_risk_calibrator()

    output_path = Path("reports/json/risk_calibrator_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\nRiskLens Alpha Risk Calibrator Training")
    print("=" * 56)
    print(f"Rows: {metrics['row_count']}")
    print(f"Train rows: {metrics['train_rows']}")
    print(f"Test rows: {metrics['test_rows']}")
    print(f"Score MAE: {metrics['score_model']['mae']}")
    print(f"Score R2: {metrics['score_model']['r2']}")
    print(f"Level accuracy: {metrics['level_model']['accuracy']}")
    print(f"Level macro F1: {metrics['level_model']['macro_f1']}")
    print(f"Severe accuracy: {metrics['severe_model']['accuracy']}")
    print(f"Severe F1: {metrics['severe_model']['f1']}")

    print("\nTop feature importance:")
    for item in metrics["feature_importance"][:8]:
        print(f"- {item['feature']}: {item['importance']}")

    print(f"\nSaved model to: {metrics['model_path']}")
    print(f"Saved metrics to: {output_path}")


if __name__ == "__main__":
    main()
