from collections import defaultdict
from backend.app.schemas import (
    AgentOpinion,
    FactorExposure,
    HoldingRisk,
    Portfolio,
    ShockScenario,
)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def risk_level_from_score(score: int) -> str:
    if score <= 30:
        return "low"
    if score <= 60:
        return "moderate"
    if score <= 80:
        return "high"
    return "severe"


def holding_risk_level(score: int) -> str:
    if score <= 30:
        return "low"
    if score <= 60:
        return "moderate"
    if score <= 80:
        return "high"
    return "very high"


def compute_concentration_risk(portfolio: Portfolio) -> float:
    # Herfindahl-Hirschman style concentration.
    # Equal 4-stock portfolio = 0.25. Concentrated portfolio gets closer to 1.
    hhi = sum(h.weight**2 for h in portfolio.holdings)
    return clamp(hhi / 0.50)


def compute_factor_exposure_score(
    portfolio: Portfolio,
    exposures: list[FactorExposure],
    scenario: ShockScenario,
) -> float:
    weights = {h.ticker: h.weight for h in portfolio.holdings}
    affected = set(scenario.affected_factors)

    weighted_total = 0.0

    for exposure in exposures:
        if exposure.factor in affected:
            weighted_total += weights.get(exposure.ticker, 0.0) * exposure.score * scenario.severity

    return clamp(weighted_total)


def compute_narrative_alignment_score(
    exposures: list[FactorExposure],
    scenario: ShockScenario,
) -> float:
    affected = set(scenario.affected_factors)
    relevant = [e for e in exposures if e.factor in affected]

    if not relevant:
        return 0.0

    avg_confidence = sum(e.confidence for e in relevant) / len(relevant)
    coverage = min(1.0, len({e.factor for e in relevant}) / max(1, len(affected)))

    return clamp(0.65 * avg_confidence + 0.35 * coverage)


def compute_correlation_risk(portfolio: Portfolio, exposures: list[FactorExposure]) -> float:
    # MVP proxy: holdings sharing the same high-level factors are treated as hidden correlation.
    factor_to_weight = defaultdict(float)

    for holding in portfolio.holdings:
        holding_exposures = [e for e in exposures if e.ticker == holding.ticker and e.score >= 0.65]
        for exposure in holding_exposures:
            factor_to_weight[exposure.factor] += holding.weight * exposure.score

    if not factor_to_weight:
        return 0.0

    top_shared_exposure = max(factor_to_weight.values())
    return clamp(top_shared_exposure)


def compute_volatility_risk(portfolio: Portfolio, exposures: list[FactorExposure]) -> float:
    # MVP proxy until live market data is added.
    # High market beta and semiconductor/growth exposure increase volatility proxy.
    weights = {h.ticker: h.weight for h in portfolio.holdings}
    vol_factors = {"market beta", "semiconductors", "growth stocks", "valuation multiples"}

    total = 0.0
    for exposure in exposures:
        if exposure.factor in vol_factors:
            total += weights.get(exposure.ticker, 0.0) * exposure.score

    return clamp(total)


def compute_agent_consensus(agent_opinions: list[AgentOpinion]) -> float:
    if not agent_opinions:
        return 0.50

    return clamp(sum(agent.confidence for agent in agent_opinions) / len(agent_opinions))


def compute_factor_contributions(
    portfolio: Portfolio,
    exposures: list[FactorExposure],
    scenario: ShockScenario,
) -> dict[str, float]:
    weights = {h.ticker: h.weight for h in portfolio.holdings}
    affected = set(scenario.affected_factors)
    raw = defaultdict(float)

    for exposure in exposures:
        if exposure.factor in affected:
            raw[exposure.factor] += weights.get(exposure.ticker, 0.0) * exposure.score * scenario.severity

    total = sum(raw.values())

    if total <= 0:
        return {}

    return {
        factor: round((value / total) * 100, 2)
        for factor, value in sorted(raw.items(), key=lambda item: item[1], reverse=True)
    }


def compute_holding_risks(
    portfolio: Portfolio,
    exposures: list[FactorExposure],
    scenario: ShockScenario,
) -> list[HoldingRisk]:
    affected = set(scenario.affected_factors)
    holding_results: list[HoldingRisk] = []

    for holding in portfolio.holdings:
        relevant = [
            e for e in exposures
            if e.ticker == holding.ticker and e.factor in affected
        ]

        raw_score = sum(e.score * e.confidence for e in relevant)
        normalized = clamp(raw_score / max(1, len(affected)))
        weighted_score = clamp(0.65 * normalized + 0.35 * holding.weight)
        final_score = round(weighted_score * scenario.severity * 100)

        reasons = []
        for exposure in sorted(relevant, key=lambda e: e.score, reverse=True)[:3]:
            reasons.append(
                f"{holding.ticker} is mapped to {exposure.factor} with exposure {exposure.score:.2f}."
            )

        if not reasons:
            reasons.append(f"{holding.ticker} has limited direct exposure to the selected scenario factors.")

        holding_results.append(
            HoldingRisk(
                ticker=holding.ticker,
                risk_score=final_score,
                risk_level=holding_risk_level(final_score),
                reasons=reasons,
            )
        )

    return sorted(holding_results, key=lambda item: item.risk_score, reverse=True)


def score_portfolio(
    portfolio: Portfolio,
    scenario: ShockScenario,
    exposures: list[FactorExposure],
    agent_opinions: list[AgentOpinion],
) -> tuple[int, str, dict[str, float], list[HoldingRisk]]:
    concentration = compute_concentration_risk(portfolio)
    factor_exposure = compute_factor_exposure_score(portfolio, exposures, scenario)
    correlation = compute_correlation_risk(portfolio, exposures)
    volatility = compute_volatility_risk(portfolio, exposures)
    narrative_alignment = compute_narrative_alignment_score(exposures, scenario)
    agent_consensus = compute_agent_consensus(agent_opinions)

    raw_score = (
        0.25 * concentration
        + 0.20 * factor_exposure
        + 0.15 * correlation
        + 0.15 * volatility
        + 0.15 * narrative_alignment
        + 0.10 * agent_consensus
    )

    score = round(100 * clamp(raw_score))
    level = risk_level_from_score(score)
    contributions = compute_factor_contributions(portfolio, exposures, scenario)
    holding_risks = compute_holding_risks(portfolio, exposures, scenario)

    return score, level, contributions, holding_risks
