from __future__ import annotations

import json
from pathlib import Path

from backend.app.ml.narrative_classifier import (
    DEFAULT_MODEL_PATH as NARRATIVE_MODEL_PATH,
    load_model_metrics as load_narrative_metrics,
)
from backend.app.ml.risk_calibrator import (
    DEFAULT_DATASET_PATH as RISK_DATASET_PATH,
    DEFAULT_MODEL_PATH as RISK_MODEL_PATH,
    load_risk_calibrator_metrics,
)
from backend.app.services.dynamic_factor_updater import run_dynamic_factor_update
from backend.app.main import load_sample_portfolio
from backend.app.services.news_aware_simulation import run_news_aware_simulation
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_generator import get_scenario


def count_jsonl_rows(path: str) -> int:
    file_path = Path(path)

    if not file_path.exists():
        return 0

    with file_path.open("r", encoding="utf-8") as file:
        return sum(1 for line in file if line.strip())


def model_status(path: str) -> dict:
    file_path = Path(path)

    return {
        "path": path,
        "exists": file_path.exists(),
        "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
    }


def load_json_report(path: str) -> dict:
    report_path = Path(path)

    if not report_path.exists():
        return {}

    return json.loads(report_path.read_text(encoding="utf-8"))


def evaluate_narrative_classifier_status() -> dict:
    status = model_status(NARRATIVE_MODEL_PATH)

    if not status["exists"]:
        return {
            "status": "missing",
            "model": status,
            "passed": False,
            "metrics": {},
            "summary": "Narrative classifier model artifact is missing.",
        }

    try:
        metrics = load_narrative_metrics()
    except Exception as error:
        return {
            "status": "error",
            "model": status,
            "passed": False,
            "metrics": {},
            "summary": str(error),
        }

    accuracy = metrics.get("accuracy", 0)
    macro_f1 = metrics.get("macro_f1", 0)

    passed = accuracy >= 0.70 and macro_f1 >= 0.70

    return {
        "status": "ok" if passed else "needs_attention",
        "model": status,
        "passed": passed,
        "metrics": {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "training_rows": metrics.get("training_rows"),
            "test_rows": metrics.get("test_rows"),
            "label_count": metrics.get("label_count"),
            "labels": metrics.get("labels", []),
        },
        "summary": (
            f"Narrative classifier accuracy={accuracy}, macro_f1={macro_f1}."
        ),
    }


def evaluate_risk_calibrator_status() -> dict:
    status = model_status(RISK_MODEL_PATH)

    if not status["exists"]:
        return {
            "status": "missing",
            "model": status,
            "passed": False,
            "metrics": {},
            "training_data_rows": count_jsonl_rows(RISK_DATASET_PATH),
            "summary": "Risk calibrator model artifact is missing.",
        }

    try:
        metrics = load_risk_calibrator_metrics()
    except Exception as error:
        return {
            "status": "error",
            "model": status,
            "passed": False,
            "metrics": {},
            "training_data_rows": count_jsonl_rows(RISK_DATASET_PATH),
            "summary": str(error),
        }

    score_mae = metrics.get("score_model", {}).get("mae", 999)
    score_r2 = metrics.get("score_model", {}).get("r2", 0)
    level_accuracy = metrics.get("level_model", {}).get("accuracy", 0)
    severe_f1 = metrics.get("severe_model", {}).get("f1", 0)

    passed = score_mae <= 10 and score_r2 >= 0.50 and level_accuracy >= 0.60 and severe_f1 >= 0.60

    return {
        "status": "ok" if passed else "needs_attention",
        "model": status,
        "passed": passed,
        "training_data_rows": count_jsonl_rows(RISK_DATASET_PATH),
        "metrics": {
            "score_mae": score_mae,
            "score_r2": score_r2,
            "level_accuracy": level_accuracy,
            "level_macro_f1": metrics.get("level_model", {}).get("macro_f1"),
            "severe_accuracy": metrics.get("severe_model", {}).get("accuracy"),
            "severe_f1": severe_f1,
            "feature_importance": metrics.get("feature_importance", [])[:8],
        },
        "summary": (
            f"Risk calibrator MAE={score_mae}, R2={score_r2}, "
            f"level_accuracy={level_accuracy}, severe_f1={severe_f1}."
        ),
    }


def evaluate_dynamic_factor_update_health() -> dict:
    try:
        result = run_dynamic_factor_update(
            articles=[
                {
                    "title": "NVDA falls after new China AI chip export restrictions",
                    "summary": "Investors worry advanced accelerator shipments could be limited.",
                    "tickers": ["NVDA"],
                }
            ],
            tickers=["NVDA", "AMD"],
        )
    except Exception as error:
        return {
            "status": "error",
            "passed": False,
            "summary": str(error),
        }

    adjustment_count = 0

    for updates in result.get("ticker_updates", {}).values():
        adjustment_count += sum(1 for item in updates if item.get("adjustment", 0) > 0)

    passed = result.get("narrative_count", 0) >= 1 and adjustment_count >= 1

    return {
        "status": "ok" if passed else "needs_attention",
        "passed": passed,
        "narrative_count": result.get("narrative_count", 0),
        "adjustment_count": adjustment_count,
        "summary": result.get("summary", ""),
    }


def evaluate_news_aware_simulation_health() -> dict:
    try:
        raw = load_sample_portfolio("ai_growth_sample")
        portfolio = normalize_portfolio(raw)
        scenario = get_scenario("ai_capex_slowdown")

        result = run_news_aware_simulation(
            portfolio=portfolio,
            scenario=scenario,
            articles=[
                {
                    "title": "Cloud giants slow AI data center spending after aggressive capex buildout",
                    "summary": "Markets reassessed GPU demand and AI infrastructure spending.",
                    "tickers": ["NVDA", "MSFT"],
                }
            ],
            use_market_data=False,
            run_ml_calibration=True,
        )
    except Exception as error:
        return {
            "status": "error",
            "passed": False,
            "summary": str(error),
        }

    simulation = result.get("result", {})
    ml_calibration = result.get("ml_calibration")

    passed = (
        result.get("news_adjusted") is True
        and simulation.get("vulnerability_score") is not None
        and result.get("dynamic_factor_update", {}).get("narrative_count", 0) >= 1
    )

    return {
        "status": "ok" if passed else "needs_attention",
        "passed": passed,
        "news_adjusted": result.get("news_adjusted"),
        "vulnerability_score": simulation.get("vulnerability_score"),
        "risk_level": simulation.get("risk_level"),
        "ml_calibration_available": ml_calibration is not None,
        "summary": simulation.get("summary", ""),
    }


def run_ml_evaluation_suite() -> dict:
    checks = {
        "narrative_classifier": evaluate_narrative_classifier_status(),
        "risk_calibrator": evaluate_risk_calibrator_status(),
        "dynamic_factor_update": evaluate_dynamic_factor_update_health(),
        "news_aware_simulation": evaluate_news_aware_simulation_health(),
    }

    passed_checks = sum(1 for item in checks.values() if item.get("passed"))
    total_checks = len(checks)

    overall_score = round(100 * passed_checks / total_checks) if total_checks else 0

    return {
        "suite_name": "RiskLens Alpha ML Evaluation Suite",
        "overall_score": overall_score,
        "passed": passed_checks == total_checks,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "checks": checks,
    }
