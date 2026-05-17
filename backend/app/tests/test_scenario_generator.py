import pytest

from backend.app.services.scenario_generator import get_scenario, list_scenarios


def test_get_scenario_returns_known_scenario():
    scenario = get_scenario("ai_capex_slowdown")

    assert scenario.name == "AI Infrastructure Spending Slowdown"
    assert scenario.severity == 0.75
    assert "AI infrastructure" in scenario.affected_factors


def test_get_scenario_rejects_unknown_scenario():
    with pytest.raises(ValueError, match="Unknown scenario_id"):
        get_scenario("unknown_scenario")


def test_list_scenarios_returns_multiple_scenarios():
    scenarios = list_scenarios()

    assert len(scenarios) >= 5
