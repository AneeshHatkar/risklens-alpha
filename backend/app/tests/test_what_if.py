from backend.app.main import load_sample_portfolio
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_generator import get_scenario
from backend.app.services.what_if import compare_what_if_portfolios


def test_what_if_comparison_returns_delta_and_safety_note():
    base_raw = load_sample_portfolio("ai_growth_sample")
    base = normalize_portfolio(base_raw)

    what_if_raw = {
        "name": "What-if Portfolio",
        "holdings": [
            {"ticker": "NVDA", "weight": 0.20},
            {"ticker": "MSFT", "weight": 0.25},
            {"ticker": "AAPL", "weight": 0.25},
            {"ticker": "SPY", "weight": 0.30},
        ],
    }
    what_if = normalize_portfolio(what_if_raw)

    scenario = get_scenario("ai_capex_slowdown")

    result = compare_what_if_portfolios(
        base_portfolio=base,
        what_if_portfolio=what_if,
        scenario=scenario,
    )

    assert "base" in result
    assert "what_if" in result
    assert "score_delta" in result
    assert "hidden_concentration_delta" in result
    assert "not a recommendation" in result["safety_note"].lower()


def test_what_if_result_has_valid_scores():
    base_raw = load_sample_portfolio("ai_growth_sample")
    base = normalize_portfolio(base_raw)

    what_if_raw = {
        "name": "What-if Portfolio",
        "holdings": [
            {"ticker": "NVDA", "weight": 0.20},
            {"ticker": "MSFT", "weight": 0.25},
            {"ticker": "AAPL", "weight": 0.25},
            {"ticker": "SPY", "weight": 0.30},
        ],
    }
    what_if = normalize_portfolio(what_if_raw)

    scenario = get_scenario("ai_capex_slowdown")

    result = compare_what_if_portfolios(
        base_portfolio=base,
        what_if_portfolio=what_if,
        scenario=scenario,
    )

    assert 0 <= result["base"]["vulnerability_score"] <= 100
    assert 0 <= result["what_if"]["vulnerability_score"] <= 100
