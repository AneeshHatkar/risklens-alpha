from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.factor_mapper import map_factors
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.risk_scoring import score_portfolio
from backend.app.services.scenario_generator import get_scenario


def test_ai_growth_portfolio_has_high_ai_capex_risk():
    raw = {
        "name": "AI Growth Sample",
        "holdings": [
            {"ticker": "NVDA", "weight": 0.35},
            {"ticker": "MSFT", "weight": 0.25},
            {"ticker": "AAPL", "weight": 0.20},
            {"ticker": "SPY", "weight": 0.20},
        ],
    }

    portfolio = normalize_portfolio(raw)
    scenario = get_scenario("ai_capex_slowdown")
    exposures = map_factors(portfolio, scenario)
    agents = run_agent_debate(portfolio, scenario, exposures)

    score, level, contributions, holding_risks = score_portfolio(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        agent_opinions=agents,
    )

    assert score >= 60
    assert level in {"high", "severe"}
    assert "AI infrastructure" in contributions
    assert holding_risks[0].ticker in {"NVDA", "MSFT"}


def test_semiconductor_portfolio_flags_semiconductor_risk():
    raw = {
        "name": "Semiconductor Sample",
        "holdings": [
            {"ticker": "NVDA", "weight": 0.40},
            {"ticker": "SMH", "weight": 0.35},
            {"ticker": "MSFT", "weight": 0.15},
            {"ticker": "SPY", "weight": 0.10},
        ],
    }

    portfolio = normalize_portfolio(raw)
    scenario = get_scenario("semiconductor_export_restriction")
    exposures = map_factors(portfolio, scenario)
    agents = run_agent_debate(portfolio, scenario, exposures)

    score, level, contributions, holding_risks = score_portfolio(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        agent_opinions=agents,
    )

    assert score >= 60
    assert "semiconductors" in contributions
    assert holding_risks[0].ticker in {"NVDA", "SMH"}
