from backend.app.main import run_simulation
from backend.app.services.agent_disagreement import (
    calculate_agent_disagreement,
    calculate_confidence_spread,
)


def test_calculate_agent_disagreement_from_simulation():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    disagreement = calculate_agent_disagreement(result.agent_opinions)

    assert 0 <= disagreement["score"] <= 100
    assert disagreement["label"] in {"low", "moderate", "high"}
    assert "summary" in disagreement


def test_confidence_spread_from_agents():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    spread = calculate_confidence_spread(result.agent_opinions)

    assert spread >= 0


def test_run_simulation_includes_agent_disagreement():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    assert result.agent_disagreement is not None
    assert "score" in result.agent_disagreement
