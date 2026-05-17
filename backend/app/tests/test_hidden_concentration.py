from backend.app.services.factor_mapper import map_factors
from backend.app.services.hidden_concentration import calculate_hidden_concentration
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_generator import get_scenario


def test_hidden_concentration_returns_valid_score():
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

    result = calculate_hidden_concentration(portfolio, exposures)

    assert 0 <= result["score"] <= 100
    assert result["level"] in {"low", "moderate", "high", "severe"}
    assert "dominant_themes" in result
    assert "explanation" in result


def test_ai_growth_sample_has_big_tech_overlap_theme():
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

    result = calculate_hidden_concentration(portfolio, exposures)
    factors = [item["factor"] for item in result["dominant_themes"]]

    assert "big-tech correlation" in factors
