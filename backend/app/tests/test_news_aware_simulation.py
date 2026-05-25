from backend.app.main import load_sample_portfolio
from backend.app.services.news_aware_simulation import (
    apply_dynamic_updates_to_exposures,
    run_news_aware_simulation,
)
from backend.app.services.factor_mapper import map_factors
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_generator import get_scenario


def test_apply_dynamic_updates_to_exposures_updates_matching_factor():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)
    scenario = get_scenario("ai_capex_slowdown")
    exposures = map_factors(portfolio, scenario)

    dynamic_update = {
        "ticker_updates": {
            "NVDA": [
                {
                    "factor": "semiconductors",
                    "dynamic_score": 1.0,
                    "dynamic_confidence": 0.99,
                    "adjustment": 0.04,
                    "exists_in_base_map": True,
                    "base_score": 0.96,
                    "narrative_evidence": [],
                }
            ]
        }
    }

    updated = apply_dynamic_updates_to_exposures(exposures, dynamic_update)

    before = [
        item for item in exposures
        if item.ticker == "NVDA" and item.factor == "semiconductors"
    ][0]

    after = [
        item for item in updated
        if item.ticker == "NVDA" and item.factor == "semiconductors"
    ][0]

    assert after.score >= before.score
    assert after.confidence >= before.confidence


def test_run_news_aware_simulation_returns_result():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)
    scenario = get_scenario("ai_capex_slowdown")

    output = run_news_aware_simulation(
        portfolio=portfolio,
        scenario=scenario,
        articles=[
            {
                "title": "NVDA falls after China chip export restrictions",
                "summary": "Investors worry AI accelerator shipments could be limited.",
                "tickers": ["NVDA"],
            }
        ],
        use_market_data=False,
        run_ml_calibration=False,
    )

    assert output["news_adjusted"] is True
    assert "result" in output
    assert "dynamic_factor_update" in output
    assert output["dynamic_factor_update"]["narrative_count"] == 1
    assert output["result"]["vulnerability_score"] >= 0
