from backend.app.schemas import AgentOpinion, FactorExposure, Portfolio


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def confidence_label(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.70:
        return "medium-high"
    if confidence >= 0.50:
        return "medium"
    return "low"


def calculate_confidence_interval(
    score: int,
    portfolio: Portfolio,
    exposures: list[FactorExposure],
    agent_opinions: list[AgentOpinion],
    market_metrics: dict | None = None,
) -> dict:
    mapped_tickers = {exposure.ticker for exposure in exposures}
    portfolio_tickers = {holding.ticker for holding in portfolio.holdings}

    factor_coverage = len(mapped_tickers & portfolio_tickers) / max(1, len(portfolio_tickers))

    if exposures:
        exposure_confidence = sum(exposure.confidence for exposure in exposures) / len(exposures)
    else:
        exposure_confidence = 0.0

    if agent_opinions:
        agent_confidence = sum(agent.confidence for agent in agent_opinions) / len(agent_opinions)
    else:
        agent_confidence = 0.0

    market_confidence = 0.50
    if market_metrics:
        missing = market_metrics.get("portfolio_metrics", {}).get("missing_tickers", [])
        missing_penalty = len(missing) / max(1, len(portfolio_tickers))
        market_confidence = clamp(1.0 - missing_penalty)

    overall_confidence = clamp(
        0.30 * factor_coverage
        + 0.25 * exposure_confidence
        + 0.25 * agent_confidence
        + 0.20 * market_confidence
    )

    # Lower confidence means wider range.
    width = round(4 + (1.0 - overall_confidence) * 18)

    lower = max(0, score - width)
    upper = min(100, score + width)

    return {
        "lower": lower,
        "upper": upper,
        "confidence": round(overall_confidence, 3),
        "label": confidence_label(overall_confidence),
        "drivers": {
            "factor_coverage": round(factor_coverage, 3),
            "exposure_confidence": round(exposure_confidence, 3),
            "agent_confidence": round(agent_confidence, 3),
            "market_confidence": round(market_confidence, 3),
        },
    }
