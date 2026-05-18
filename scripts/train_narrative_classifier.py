import json
from pathlib import Path

from backend.app.ml.narrative_classifier import train_narrative_classifier


def main():
    metrics = train_narrative_classifier()

    output_path = Path("reports/json/narrative_classifier_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\nRiskLens Alpha Narrative Classifier Training")
    print("=" * 56)
    print(f"Training rows: {metrics['training_rows']}")
    print(f"Test rows: {metrics['test_rows']}")
    print(f"Labels: {metrics['label_count']}")
    print(f"Accuracy: {metrics['accuracy']}")
    print(f"Macro F1: {metrics['macro_f1']}")
    print(f"Saved model to: {metrics['model_path']}")
    print(f"Saved metrics to: {output_path}")


if __name__ == "__main__":
    main()
