from backend.app.schemas import Portfolio, ShockScenario
from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.factor_mapper import map_factors
from backend.app.services.hidden_concentration import calculate_hidden_concentration
from backend.app.services.risk_scoring import score_portfolio


def run_single_portfolio_score(
    portfolio: Portfolio,
    scenario: ShockScenario,
    market_metrics: dict | None = None,
) -> dict:
    exposures = map_factors(portfolio, scenario)
    agents = run_agent_debate(portfolio, scenario, exposures)

    score, risk_level, factor_contributions, holding_risks = score_portfolio(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        agent_opinions=agents,
        market_metrics=market_metrics,
    )

    hidden_concentration = calculate_hidden_concentration(
        portfolio=portfolio,
        exposures=exposures,
    )

    return {
        "portfolio_name": portfolio.name,
        "vulnerability_score": score,
        "risk_level": risk_level,
        "dominant_factors": list(factor_contributions.keys())[:5],
        "most_vulnerable_holdings": [
            holding.ticker for holding in holding_risks
            if holding.risk_score >= 20
        ][:3],
        "hidden_concentration": hidden_concentration,
    }


def compare_what_if_portfolios(
    base_portfolio: Portfolio,
    what_if_portfolio: Portfolio,
    scenario: ShockScenario,
    market_metrics: dict | None = None,
) -> dict:
    base_result = run_single_portfolio_score(
        portfolio=base_portfolio,
        scenario=scenario,
        market_metrics=market_metrics,
    )

    what_if_result = run_single_portfolio_score(
        portfolio=what_if_portfolio,
        scenario=scenario,
        market_metrics=market_metrics,
    )

    score_delta = (
        what_if_result["vulnerability_score"]
        - base_result["vulnerability_score"]
    )

    hidden_concentration_delta = (
        what_if_result["hidden_concentration"]["score"]
        - base_result["hidden_concentration"]["score"]
    )

    if score_delta < 0:
        point_word = "point" if abs(score_delta) == 1 else "points"
        interpretation = (
            f"The hypothetical portfolio reduces simulated vulnerability by "
            f"{abs(score_delta)} {point_word} under this scenario."
        )
    elif score_delta > 0:
        point_word = "point" if score_delta == 1 else "points"
        interpretation = (
            f"The hypothetical portfolio increases simulated vulnerability by "
            f"{score_delta} {point_word} under this scenario."
        )
    else:
        interpretation = (
            "The hypothetical portfolio has the same simulated vulnerability "
            "under this scenario."
        )

    return {
        "scenario_name": scenario.name,
        "base": base_result,
        "what_if": what_if_result,
        "score_delta": score_delta,
        "hidden_concentration_delta": hidden_concentration_delta,
        "interpretation": interpretation,
        "safety_note": (
            "This is hypothetical scenario analysis only. It is not a recommendation "
            "to buy, sell, or rebalance any security."
        ),
    }
