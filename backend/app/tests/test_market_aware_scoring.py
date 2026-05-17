from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.factor_mapper import map_factors
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.risk_scoring import score_portfolio
from backend.app.services.scenario_generator import get_scenario


def test_market_metrics_are_included_in_holding_reasons():
    raw = {
        "name": "AI Growth Sample",
        "holdings": [
            {"ticker": "NVDA", "weight": 0.35},
            {"ticker": "MSFT", "weight": 0.25},
            {"ticker": "AAPL", "weight": 0.20},
            {"ticker": "SPY", "weight": 0.20},
        ],
    }

    market_metrics = {
        "portfolio_metrics": {
            "portfolio_volatility": 0.30,
            "average_pairwise_correlation": 0.55,
            "benchmark": "SPY",
            "start": "2024-01-01",
            "end": None,
            "missing_tickers": [],
        },
        "asset_metrics": {
            "NVDA": {
                "available": True,
                "volatility": 0.50,
                "beta": 2.0,
                "max_drawdown": -0.35,
                "cumulative_return": 1.2,
            }
        },
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
        market_metrics=market_metrics,
    )

    nvda = next(item for item in holding_risks if item.ticker == "NVDA")
    joined_reasons = " ".join(nvda.reasons).lower()

    assert score >= 60
    assert level in {"high", "severe"}
    assert "market metrics" in joined_reasons
    assert "beta" in joined_reasons
