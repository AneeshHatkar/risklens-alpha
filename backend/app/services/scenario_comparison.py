from backend.app.schemas import Portfolio
from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.factor_mapper import map_factors
from backend.app.services.risk_scoring import score_portfolio
from backend.app.services.scenario_generator import SCENARIOS


def compare_scenarios(
    portfolio: Portfolio,
    market_metrics: dict | None = None,
) -> list[dict]:
    results = []

    for scenario_id, scenario in SCENARIOS.items():
        exposures = map_factors(portfolio, scenario)
        agent_opinions = run_agent_debate(portfolio, scenario, exposures)

        score, risk_level, factor_contributions, holding_risks = score_portfolio(
            portfolio=portfolio,
            scenario=scenario,
            exposures=exposures,
            agent_opinions=agent_opinions,
            market_metrics=market_metrics,
        )

        most_vulnerable_holdings = [
            holding.ticker for holding in holding_risks
            if holding.risk_score >= 20
        ][:3]

        results.append(
            {
                "scenario_id": scenario_id,
                "scenario_name": scenario.name,
                "severity": scenario.severity,
                "vulnerability_score": score,
                "risk_level": risk_level,
                "dominant_factors": list(factor_contributions.keys())[:5],
                "most_vulnerable_holdings": most_vulnerable_holdings,
            }
        )

    return sorted(
        results,
        key=lambda item: item["vulnerability_score"],
        reverse=True,
    )
