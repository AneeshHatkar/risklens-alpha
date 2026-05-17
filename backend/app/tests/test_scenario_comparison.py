from backend.app.main import load_sample_portfolio
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_comparison import compare_scenarios


def test_compare_scenarios_returns_ranked_results():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)

    results = compare_scenarios(portfolio)

    assert len(results) >= 5
    assert results[0]["vulnerability_score"] >= results[-1]["vulnerability_score"]
    assert "scenario_id" in results[0]
    assert "scenario_name" in results[0]
    assert "risk_level" in results[0]


def test_compare_scenarios_includes_ai_capex_scenario():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)

    results = compare_scenarios(portfolio)
    scenario_ids = [item["scenario_id"] for item in results]

    assert "ai_capex_slowdown" in scenario_ids
