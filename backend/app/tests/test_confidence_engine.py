from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.confidence_engine import calculate_confidence_interval
from backend.app.services.factor_mapper import map_factors
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_generator import get_scenario


def test_confidence_interval_has_valid_bounds():
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

    interval = calculate_confidence_interval(
        score=70,
        portfolio=portfolio,
        exposures=exposures,
        agent_opinions=agents,
        market_metrics=None,
    )

    assert 0 <= interval["lower"] <= 70
    assert 70 <= interval["upper"] <= 100
    assert 0 <= interval["confidence"] <= 1
    assert interval["label"] in {"high", "medium-high", "medium", "low"}
    assert "drivers" in interval
