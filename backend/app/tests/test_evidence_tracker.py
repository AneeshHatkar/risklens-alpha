from backend.app.main import run_simulation
from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.evidence_tracker import build_simulation_evidence
from backend.app.services.factor_mapper import map_factors
from backend.app.services.hidden_concentration import calculate_hidden_concentration
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.risk_scoring import score_portfolio
from backend.app.services.scenario_generator import get_scenario


def test_evidence_tracker_builds_multiple_evidence_types():
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
    _, _, _, holding_risks = score_portfolio(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        agent_opinions=agents,
    )
    hidden = calculate_hidden_concentration(portfolio, exposures)

    evidence = build_simulation_evidence(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        holding_risks=holding_risks,
        agent_opinions=agents,
        hidden_concentration=hidden,
        market_metrics=None,
    )

    evidence_types = {item.evidence_type for item in evidence}

    assert "scenario_rule" in evidence_types
    assert "factor_mapping" in evidence_types
    assert "holding_risk" in evidence_types
    assert "hidden_concentration" in evidence_types
    assert "agent_opinion" in evidence_types


def test_run_simulation_includes_evidence_items():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    assert len(result.evidence_items) > 0

    evidence_types = {item.evidence_type for item in result.evidence_items}

    assert "scenario_rule" in evidence_types
    assert "factor_mapping" in evidence_types
