from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


DEFAULT_MODEL_PATH = "outputs/models/narrative_classifier.joblib"
DEFAULT_DATASET_PATH = "datasets/news/sample_market_news.jsonl"


def load_news_dataset(path: str = DEFAULT_DATASET_PATH) -> list[dict]:
    rows = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    return rows


def article_to_text(row: dict) -> str:
    title = row.get("title", "")
    summary = row.get("summary", "")
    return f"{title}. {summary}".strip()


def build_training_arrays(rows: list[dict]) -> tuple[list[str], list[str]]:
    texts = [article_to_text(row) for row in rows]
    labels = [row["label"] for row in rows]
    return texts, labels


def build_narrative_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=5000,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def train_narrative_classifier(
    dataset_path: str = DEFAULT_DATASET_PATH,
    model_path: str = DEFAULT_MODEL_PATH,
    test_size: float = 0.25,
    random_state: int = 42,
) -> dict:
    rows = load_news_dataset(dataset_path)
    texts, labels = build_training_arrays(rows)

    x_train, x_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    model = build_narrative_pipeline()
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)

    metrics = {
        "dataset_path": dataset_path,
        "model_path": model_path,
        "training_rows": len(x_train),
        "test_rows": len(x_test),
        "label_count": len(set(labels)),
        "labels": sorted(set(labels)),
        "accuracy": round(accuracy_score(y_test, predictions), 4),
        "macro_f1": round(f1_score(y_test, predictions, average="macro"), 4),
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            y_test,
            predictions,
            labels=sorted(set(labels)),
        ).tolist(),
    }

    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "labels": sorted(set(labels)),
            "metrics": metrics,
        },
        model_path,
    )

    return metrics


def load_narrative_model(model_path: str = DEFAULT_MODEL_PATH) -> dict:
    path = Path(model_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Narrative classifier model not found at {model_path}. "
            "Run scripts/train_narrative_classifier.py first."
        )

    return joblib.load(path)


def predict_narrative(
    title: str,
    summary: str = "",
    model_path: str = DEFAULT_MODEL_PATH,
    top_k: int = 3,
) -> dict:
    artifact = load_narrative_model(model_path)
    model = artifact["model"]

    text = f"{title}. {summary}".strip()

    predicted_label = model.predict([text])[0]

    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)

    ranked = sorted(
        [
            {
                "label": label,
                "probability": round(float(probability), 4),
            }
            for label, probability in zip(classes, probabilities)
        ],
        key=lambda item: item["probability"],
        reverse=True,
    )

    return {
        "title": title,
        "summary": summary,
        "predicted_label": predicted_label,
        "confidence": ranked[0]["probability"],
        "top_labels": ranked[:top_k],
        "model_path": model_path,
    }


def load_model_metrics(model_path: str = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    artifact = load_narrative_model(model_path)
    return artifact.get("metrics", {})
