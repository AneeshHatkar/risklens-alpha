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


def normalize_range(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return clamp((value - low) / (high - low))


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


def compute_correlation_risk(
    portfolio: Portfolio,
    exposures: list[FactorExposure],
    market_metrics: dict | None = None,
) -> float:
    if market_metrics:
        corr = market_metrics.get("portfolio_metrics", {}).get("average_pairwise_correlation")
        if corr is not None:
            return normalize_range(abs(float(corr)), 0.10, 0.85)

    factor_to_weight = defaultdict(float)

    for holding in portfolio.holdings:
        holding_exposures = [e for e in exposures if e.ticker == holding.ticker and e.score >= 0.65]
        for exposure in holding_exposures:
            factor_to_weight[exposure.factor] += holding.weight * exposure.score

    if not factor_to_weight:
        return 0.0

    return clamp(max(factor_to_weight.values()))


def compute_volatility_risk(
    portfolio: Portfolio,
    exposures: list[FactorExposure],
    market_metrics: dict | None = None,
) -> float:
    if market_metrics:
        vol = market_metrics.get("portfolio_metrics", {}).get("portfolio_volatility")
        if vol is not None:
            # 10% annualized volatility is low, 45%+ is high for an equity portfolio.
            return normalize_range(float(vol), 0.10, 0.45)

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
    market_metrics: dict | None = None,
) -> list[HoldingRisk]:
    affected = set(scenario.affected_factors)
    asset_metrics = market_metrics.get("asset_metrics", {}) if market_metrics else {}

    holding_results: list[HoldingRisk] = []

    for holding in portfolio.holdings:
        relevant = [
            e for e in exposures
            if e.ticker == holding.ticker and e.factor in affected
        ]

        factor_score = sum(e.score * e.confidence for e in relevant)
        factor_score = clamp(factor_score / max(1, len(affected)))

        market_score = 0.0
        ticker_metrics = asset_metrics.get(holding.ticker)

        if ticker_metrics and ticker_metrics.get("available"):
            beta_score = normalize_range(abs(float(ticker_metrics.get("beta", 0.0))), 0.50, 2.00)
            vol_score = normalize_range(float(ticker_metrics.get("volatility", 0.0)), 0.10, 0.60)
            drawdown_score = normalize_range(abs(float(ticker_metrics.get("max_drawdown", 0.0))), 0.05, 0.45)
            market_score = clamp(0.35 * beta_score + 0.35 * vol_score + 0.30 * drawdown_score)

        weighted_score = clamp(
            0.55 * factor_score
            + 0.25 * market_score
            + 0.20 * holding.weight
        )

        final_score = round(weighted_score * scenario.severity * 100)

        reasons = []

        for exposure in sorted(relevant, key=lambda e: e.score, reverse=True)[:3]:
            reasons.append(
                f"{holding.ticker} is mapped to {exposure.factor} with exposure {exposure.score:.2f}."
            )

        if ticker_metrics and ticker_metrics.get("available"):
            reasons.append(
                f"Market metrics: beta {ticker_metrics['beta']}, volatility {ticker_metrics['volatility']}, "
                f"max drawdown {ticker_metrics['max_drawdown']}."
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
    market_metrics: dict | None = None,
) -> tuple[int, str, dict[str, float], list[HoldingRisk]]:
    concentration = compute_concentration_risk(portfolio)
    factor_exposure = compute_factor_exposure_score(portfolio, exposures, scenario)
    correlation = compute_correlation_risk(portfolio, exposures, market_metrics)
    volatility = compute_volatility_risk(portfolio, exposures, market_metrics)
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
    holding_risks = compute_holding_risks(portfolio, exposures, scenario, market_metrics)

    return score, level, contributions, holding_risks
