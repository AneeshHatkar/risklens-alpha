from __future__ import annotations

import json
from pathlib import Path

from backend.app.main import run_simulation


FORBIDDEN_ADVICE_PHRASES = [
    "you should buy",
    "you should sell",
    "guaranteed return",
    "will definitely go up",
    "will definitely crash",
    "must buy",
    "must sell",
    "risk-free",
]


def load_evaluation_cases(path: str | None = None) -> list[dict]:
    if path is None:
        path = str(Path(__file__).resolve().parents[1] / "evaluation" / "evaluation_cases.json")

    return json.loads(Path(path).read_text(encoding="utf-8"))


def score_overlap(actual: list[str], expected: list[str]) -> float:
    if not expected:
        return 1.0

    actual_set = {item.lower() for item in actual}
    expected_set = {item.lower() for item in expected}

    matched = len(actual_set.intersection(expected_set))
    return matched / len(expected_set)


def evaluate_no_advice_safety(result) -> dict:
    text_parts = [
        result.summary,
        result.disclaimer,
        *[agent.thesis for agent in result.agent_opinions],
        *[item.claim for item in result.evidence_items],
    ]

    text = " ".join(text_parts).lower()
    violations = [phrase for phrase in FORBIDDEN_ADVICE_PHRASES if phrase in text]

    return {
        "score": 100 if not violations else 0,
        "violations": violations,
        "passed": not violations,
    }


def evaluate_agent_schema(result) -> dict:
    issues = []

    for agent in result.agent_opinions:
        if not agent.agent_name:
            issues.append("Agent missing name.")
        if not agent.thesis:
            issues.append(f"{agent.agent_name} missing thesis.")
        if not isinstance(agent.affected_holdings, list):
            issues.append(f"{agent.agent_name} affected_holdings is not a list.")
        if not 0 <= agent.confidence <= 1:
            issues.append(f"{agent.agent_name} confidence out of range.")
        if not isinstance(agent.evidence, list):
            issues.append(f"{agent.agent_name} evidence is not a list.")
        if not isinstance(agent.risks, list):
            issues.append(f"{agent.agent_name} risks is not a list.")

    score = 100 if not issues else max(0, 100 - 10 * len(issues))

    return {
        "score": score,
        "issues": issues,
        "passed": not issues,
    }


def evaluate_evidence_grounding(result) -> dict:
    evidence_items = result.evidence_items

    if not evidence_items:
        return {
            "score": 0,
            "passed": False,
            "evidence_count": 0,
            "evidence_types": [],
            "issues": ["No evidence items found."],
        }

    evidence_types = {item.evidence_type for item in evidence_items}

    required_types = {
        "scenario_rule",
        "factor_mapping",
        "holding_risk",
        "agent_opinion",
    }

    missing = sorted(required_types - evidence_types)

    score = round(100 * (1 - len(missing) / len(required_types)))

    return {
        "score": score,
        "passed": not missing,
        "evidence_count": len(evidence_items),
        "evidence_types": sorted(evidence_types),
        "issues": [f"Missing evidence type: {item}" for item in missing],
    }


def evaluate_report_completeness(result) -> dict:
    issues = []

    if result.vulnerability_score is None:
        issues.append("Missing vulnerability score.")
    if not result.risk_level:
        issues.append("Missing risk level.")
    if not result.dominant_factors:
        issues.append("Missing dominant factors.")
    if not result.holding_risks:
        issues.append("Missing holding risks.")
    if not result.agent_opinions:
        issues.append("Missing agent opinions.")
    if result.confidence_interval is None:
        issues.append("Missing confidence interval.")
    if result.hidden_concentration is None:
        issues.append("Missing hidden concentration.")
    if not result.disclaimer:
        issues.append("Missing disclaimer.")

    score = max(0, 100 - 12 * len(issues))

    return {
        "score": score,
        "issues": issues,
        "passed": not issues,
    }


def evaluate_single_case(case: dict, use_market_data: bool = False) -> dict:
    result = run_simulation(
        portfolio_id=case["portfolio_id"],
        scenario_id=case["scenario_id"],
        use_market_data=use_market_data,
    )

    factor_match = score_overlap(
        actual=result.dominant_factors,
        expected=case.get("expected_factors", []),
    )

    holding_match = score_overlap(
        actual=result.most_vulnerable_holdings,
        expected=case.get("expected_holdings", []),
    )

    score_passed = result.vulnerability_score >= case.get("expected_min_score", 0)
    risk_level_passed = result.risk_level in case.get("expected_risk_levels", [])

    scenario_consistency_score = round(
        100
        * (
            0.35 * factor_match
            + 0.25 * holding_match
            + 0.20 * int(score_passed)
            + 0.20 * int(risk_level_passed)
        )
    )

    evidence = evaluate_evidence_grounding(result)
    agent_schema = evaluate_agent_schema(result)
    safety = evaluate_no_advice_safety(result)
    completeness = evaluate_report_completeness(result)

    overall_score = round(
        0.35 * scenario_consistency_score
        + 0.25 * evidence["score"]
        + 0.15 * agent_schema["score"]
        + 0.15 * safety["score"]
        + 0.10 * completeness["score"]
    )

    passed = (
        overall_score >= 80
        and evidence["passed"]
        and agent_schema["passed"]
        and safety["passed"]
        and completeness["passed"]
    )

    return {
        "case_id": case["case_id"],
        "description": case.get("description", ""),
        "portfolio_id": case["portfolio_id"],
        "scenario_id": case["scenario_id"],
        "overall_score": overall_score,
        "passed": passed,
        "scenario_consistency": {
            "score": scenario_consistency_score,
            "factor_match": round(factor_match, 3),
            "holding_match": round(holding_match, 3),
            "score_passed": score_passed,
            "risk_level_passed": risk_level_passed,
            "actual_score": result.vulnerability_score,
            "actual_risk_level": result.risk_level,
            "actual_factors": result.dominant_factors,
            "actual_holdings": result.most_vulnerable_holdings,
        },
        "evidence_grounding": evidence,
        "agent_schema_validity": agent_schema,
        "no_advice_safety": safety,
        "report_completeness": completeness,
    }


def run_evaluation_suite(use_market_data: bool = False) -> dict:
    cases = load_evaluation_cases()
    case_results = [
        evaluate_single_case(case, use_market_data=use_market_data)
        for case in cases
    ]

    if case_results:
        overall_score = round(
            sum(item["overall_score"] for item in case_results) / len(case_results)
        )
    else:
        overall_score = 0

    passed_cases = sum(1 for item in case_results if item["passed"])
    failed_cases = [
        item["case_id"]
        for item in case_results
        if not item["passed"]
    ]

    return {
        "suite_name": "RiskLens Alpha Evaluation Suite",
        "case_count": len(case_results),
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "overall_score": overall_score,
        "passed": len(failed_cases) == 0,
        "results": case_results,
    }
