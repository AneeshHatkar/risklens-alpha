from __future__ import annotations

from collections import Counter

from backend.app.schemas import AgentOpinion


def calculate_confidence_spread(agent_opinions: list[AgentOpinion]) -> float:
    if not agent_opinions:
        return 0.0

    confidences = [agent.confidence for agent in agent_opinions]

    return round(max(confidences) - min(confidences), 4)


def calculate_holding_disagreement(agent_opinions: list[AgentOpinion]) -> float:
    if not agent_opinions:
        return 0.0

    all_holdings = []

    for agent in agent_opinions:
        all_holdings.extend(agent.affected_holdings)

    if not all_holdings:
        return 0.0

    counts = Counter(all_holdings)
    agent_count = len(agent_opinions)

    # If every important holding is mentioned by most agents, disagreement is low.
    average_support = sum(count / agent_count for count in counts.values()) / len(counts)
    disagreement = 1.0 - average_support

    return round(max(0.0, min(1.0, disagreement)), 4)


def calculate_risk_theme_disagreement(agent_opinions: list[AgentOpinion]) -> float:
    if not agent_opinions:
        return 0.0

    all_risks = []

    for agent in agent_opinions:
        all_risks.extend([risk.lower() for risk in agent.risks])

    if not all_risks:
        return 0.0

    counts = Counter(all_risks)
    agent_count = len(agent_opinions)

    average_support = sum(count / agent_count for count in counts.values()) / len(counts)
    disagreement = 1.0 - average_support

    return round(max(0.0, min(1.0, disagreement)), 4)


def disagreement_label(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "moderate"
    return "low"


def calculate_agent_disagreement(agent_opinions: list[AgentOpinion]) -> dict:
    if not agent_opinions:
        return {
            "score": 0,
            "label": "none",
            "confidence_spread": 0.0,
            "holding_disagreement": 0.0,
            "risk_theme_disagreement": 0.0,
            "summary": "No agent opinions were available to compare.",
        }

    confidence_spread = calculate_confidence_spread(agent_opinions)
    holding_disagreement = calculate_holding_disagreement(agent_opinions)
    risk_theme_disagreement = calculate_risk_theme_disagreement(agent_opinions)

    raw_score = (
        0.40 * confidence_spread
        + 0.35 * holding_disagreement
        + 0.25 * risk_theme_disagreement
    )

    score = round(raw_score * 100)
    label = disagreement_label(score)

    summary = build_disagreement_summary(
        score=score,
        label=label,
        confidence_spread=confidence_spread,
        holding_disagreement=holding_disagreement,
        risk_theme_disagreement=risk_theme_disagreement,
    )

    return {
        "score": score,
        "label": label,
        "confidence_spread": confidence_spread,
        "holding_disagreement": holding_disagreement,
        "risk_theme_disagreement": risk_theme_disagreement,
        "summary": summary,
    }


def build_disagreement_summary(
    score: int,
    label: str,
    confidence_spread: float,
    holding_disagreement: float,
    risk_theme_disagreement: float,
) -> str:
    return (
        f"Agent disagreement is {label} at {score}/100. "
        f"Confidence spread is {confidence_spread:.2f}, holding disagreement is "
        f"{holding_disagreement:.2f}, and risk-theme disagreement is {risk_theme_disagreement:.2f}."
    )
