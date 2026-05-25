from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, classification_report, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


DEFAULT_DATASET_PATH = "datasets/risk/risk_calibration_training_data.jsonl"
DEFAULT_MODEL_PATH = "outputs/models/risk_calibrator.joblib"


RISK_LEVEL_TO_ID = {
    "low": 0,
    "moderate": 1,
    "high": 2,
    "severe": 3,
}

ID_TO_RISK_LEVEL = {value: key for key, value in RISK_LEVEL_TO_ID.items()}


FEATURE_COLUMNS = [
    "scenario_severity",
    "portfolio_volatility",
    "average_pairwise_correlation",
    "hidden_concentration_score",
    "confidence_lower",
    "confidence_upper",
    "confidence_width",
    "agent_disagreement_score",
    "factor_count",
    "holding_risk_avg",
    "holding_risk_max",
    "market_data_available",
]


def load_risk_training_rows(path: str = DEFAULT_DATASET_PATH) -> list[dict]:
    rows = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    return rows


def rows_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def build_features_from_simulation_result(result) -> dict:
    market_metrics = result.market_metrics or {}
    portfolio_metrics = market_metrics.get("portfolio_metrics", {})

    confidence = result.confidence_interval or {}
    hidden = result.hidden_concentration or {}
    agent_disagreement = result.agent_disagreement or {}

    holding_scores = [holding.risk_score for holding in result.holding_risks]

    confidence_lower = confidence.get("lower", result.vulnerability_score)
    confidence_upper = confidence.get("upper", result.vulnerability_score)

    return {
        "scenario_severity": float(result.scenario.severity),
        "portfolio_volatility": float(portfolio_metrics.get("portfolio_volatility", 0.0) or 0.0),
        "average_pairwise_correlation": float(portfolio_metrics.get("average_pairwise_correlation", 0.0) or 0.0),
        "hidden_concentration_score": float(hidden.get("score", 0.0) or 0.0),
        "confidence_lower": float(confidence_lower or 0.0),
        "confidence_upper": float(confidence_upper or 0.0),
        "confidence_width": float((confidence_upper or 0.0) - (confidence_lower or 0.0)),
        "agent_disagreement_score": float(agent_disagreement.get("score", 0.0) or 0.0),
        "factor_count": float(len(result.dominant_factors)),
        "holding_risk_avg": float(sum(holding_scores) / len(holding_scores)) if holding_scores else 0.0,
        "holding_risk_max": float(max(holding_scores)) if holding_scores else 0.0,
        "market_data_available": 1.0 if market_metrics else 0.0,
    }


def build_training_data_from_results(results: list) -> list[dict]:
    rows = []

    for result in results:
        features = build_features_from_simulation_result(result)

        row = {
            **features,
            "target_score": int(result.vulnerability_score),
            "target_level": result.risk_level,
            "target_level_id": RISK_LEVEL_TO_ID.get(result.risk_level, 0),
            "severe_label": 1 if result.vulnerability_score >= 80 else 0,
            "portfolio_name": result.portfolio_name,
            "scenario_name": result.scenario.name,
        }
        rows.append(row)

    return rows


def train_risk_calibrator(
    dataset_path: str = DEFAULT_DATASET_PATH,
    model_path: str = DEFAULT_MODEL_PATH,
    test_size: float = 0.30,
    random_state: int = 42,
) -> dict:
    rows = load_risk_training_rows(dataset_path)
    df = rows_to_dataframe(rows)

    x = df[FEATURE_COLUMNS]
    y_score = df["target_score"]
    y_level = df["target_level_id"]
    y_severe = df["severe_label"]

    level_counts = y_level.value_counts()
    can_stratify = len(level_counts) > 1 and level_counts.min() >= 2

    x_train, x_test, y_score_train, y_score_test, y_level_train, y_level_test, y_severe_train, y_severe_test = train_test_split(
        x,
        y_score,
        y_level,
        y_severe,
        test_size=test_size,
        random_state=random_state,
        stratify=y_level if can_stratify else None,
    )

    score_model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=120,
                    random_state=random_state,
                    max_depth=6,
                ),
            ),
        ]
    )

    level_model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=120,
                    random_state=random_state,
                    max_depth=6,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    severe_model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=120,
                    random_state=random_state,
                    max_depth=6,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    score_model.fit(x_train, y_score_train)
    level_model.fit(x_train, y_level_train)
    severe_model.fit(x_train, y_severe_train)

    score_predictions = score_model.predict(x_test)
    level_predictions = level_model.predict(x_test)
    severe_predictions = severe_model.predict(x_test)

    score_mae = mean_absolute_error(y_score_test, score_predictions)
    score_r2 = r2_score(y_score_test, score_predictions) if len(y_score_test) > 1 else 0.0

    level_accuracy = accuracy_score(y_level_test, level_predictions)
    level_macro_f1 = f1_score(y_level_test, level_predictions, average="macro", zero_division=0)

    severe_accuracy = accuracy_score(y_severe_test, severe_predictions)
    severe_f1 = f1_score(y_severe_test, severe_predictions, zero_division=0)

    feature_importances = extract_feature_importance(score_model)

    metrics = {
        "dataset_path": dataset_path,
        "model_path": model_path,
        "row_count": len(df),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "feature_columns": FEATURE_COLUMNS,
        "score_model": {
            "mae": round(float(score_mae), 4),
            "r2": round(float(score_r2), 4),
        },
        "level_model": {
            "accuracy": round(float(level_accuracy), 4),
            "macro_f1": round(float(level_macro_f1), 4),
            "classification_report": classification_report(
                y_level_test,
                level_predictions,
                output_dict=True,
                zero_division=0,
            ),
        },
        "severe_model": {
            "accuracy": round(float(severe_accuracy), 4),
            "f1": round(float(severe_f1), 4),
        },
        "feature_importance": feature_importances,
    }

    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "score_model": score_model,
            "level_model": level_model,
            "severe_model": severe_model,
            "feature_columns": FEATURE_COLUMNS,
            "metrics": metrics,
        },
        model_path,
    )

    return metrics


def extract_feature_importance(score_model: Pipeline) -> list[dict]:
    model = score_model.named_steps["model"]
    importances = model.feature_importances_

    ranked = sorted(
        [
            {
                "feature": feature,
                "importance": round(float(importance), 4),
            }
            for feature, importance in zip(FEATURE_COLUMNS, importances)
        ],
        key=lambda item: item["importance"],
        reverse=True,
    )

    return ranked


def load_risk_calibrator(model_path: str = DEFAULT_MODEL_PATH) -> dict:
    path = Path(model_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Risk calibrator model not found at {model_path}. "
            "Run scripts/train_risk_calibrator.py first."
        )

    return joblib.load(path)


def predict_calibrated_risk_from_features(
    features: dict,
    model_path: str = DEFAULT_MODEL_PATH,
) -> dict:
    artifact = load_risk_calibrator(model_path)
    x = pd.DataFrame([{column: float(features.get(column, 0.0) or 0.0) for column in artifact["feature_columns"]}])

    score_prediction = float(artifact["score_model"].predict(x)[0])
    level_prediction_id = int(artifact["level_model"].predict(x)[0])

    severe_model = artifact["severe_model"]
    severe_probability = 0.0

    if hasattr(severe_model, "predict_proba"):
        severe_probability = float(severe_model.predict_proba(x)[0][1])
    else:
        severe_probability = float(severe_model.predict(x)[0])

    calibrated_score = round(max(0.0, min(100.0, score_prediction)))
    calibrated_level = ID_TO_RISK_LEVEL.get(level_prediction_id, "low")

    return {
        "calibrated_score": calibrated_score,
        "calibrated_level": calibrated_level,
        "severe_probability": round(severe_probability, 4),
        "features_used": {column: float(x.iloc[0][column]) for column in artifact["feature_columns"]},
        "model_path": model_path,
    }


def predict_calibrated_risk_from_result(
    result,
    model_path: str = DEFAULT_MODEL_PATH,
) -> dict:
    features = build_features_from_simulation_result(result)
    prediction = predict_calibrated_risk_from_features(features, model_path=model_path)

    prediction["base_score"] = result.vulnerability_score
    prediction["base_level"] = result.risk_level

    return prediction


def load_risk_calibrator_metrics(model_path: str = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    artifact = load_risk_calibrator(model_path)
    return artifact.get("metrics", {})
