from backend.app.ml.narrative_classifier import predict_narrative


def main():
    examples = [
        {
            "title": "Chip stocks fall after new AI export controls",
            "summary": "Investors worry that advanced GPU shipments to China could be restricted.",
        },
        {
            "title": "Treasury yields rise after hot inflation report",
            "summary": "Growth stocks declined as investors reduced expectations for rate cuts.",
        },
        {
            "title": "Cloud companies warn customers are optimizing spending",
            "summary": "Enterprise cloud growth is expected to slow as budgets tighten.",
        },
    ]

    print("\nRiskLens Alpha Narrative Classifier Predictions")
    print("=" * 56)

    for item in examples:
        result = predict_narrative(
            title=item["title"],
            summary=item["summary"],
        )

        print(f"\nTitle: {item['title']}")
        print(f"Prediction: {result['predicted_label']}")
        print(f"Confidence: {result['confidence']}")
        print("Top labels:")
        for label in result["top_labels"]:
            print(f"- {label['label']}: {label['probability']}")


if __name__ == "__main__":
    main()
