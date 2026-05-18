from pathlib import Path

from backend.app.ml.narrative_classifier import (
    load_news_dataset,
    predict_narrative,
    train_narrative_classifier,
)


def test_load_news_dataset():
    rows = load_news_dataset()

    assert len(rows) >= 30
    assert "title" in rows[0]
    assert "summary" in rows[0]
    assert "label" in rows[0]


def test_train_narrative_classifier_creates_model(tmp_path):
    model_path = tmp_path / "narrative_classifier.joblib"

    metrics = train_narrative_classifier(
        model_path=str(model_path),
        test_size=0.25,
    )

    assert model_path.exists()
    assert metrics["accuracy"] >= 0
    assert metrics["macro_f1"] >= 0
    assert metrics["label_count"] >= 5


def test_predict_narrative_after_training(tmp_path):
    model_path = tmp_path / "narrative_classifier.joblib"

    train_narrative_classifier(model_path=str(model_path))

    result = predict_narrative(
        title="Chip stocks decline after export restriction news",
        summary="Investors worry about advanced AI chip sales to China.",
        model_path=str(model_path),
    )

    assert "predicted_label" in result
    assert 0 <= result["confidence"] <= 1
    assert len(result["top_labels"]) >= 1
