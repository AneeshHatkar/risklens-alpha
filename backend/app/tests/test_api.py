from fastapi.testclient import TestClient

from backend.app.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_scenarios_endpoint_returns_scenarios():
    response = client.get("/scenarios")

    assert response.status_code == 200
    data = response.json()

    assert "ai_capex_slowdown" in data
    assert "higher_for_longer_rates" in data


def test_sample_portfolios_endpoint_returns_samples():
    response = client.get("/portfolios/samples")

    assert response.status_code == 200
    data = response.json()

    assert "ai_growth_sample" in data
    assert "semiconductor_sample" in data


def test_simulate_endpoint_returns_risk_result():
    response = client.post(
        "/simulate",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "save_json": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["portfolio_name"] == "AI Growth Sample Portfolio"
    assert data["vulnerability_score"] >= 60
    assert data["risk_level"] in {"high", "severe"}
    assert "NVDA" in data["most_vulnerable_holdings"]


def test_simulate_endpoint_rejects_bad_scenario():
    response = client.post(
        "/simulate",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "bad_scenario",
            "save_json": False,
        },
    )

    assert response.status_code == 400
    assert "Unknown scenario_id" in response.json()["detail"]


def test_simulate_endpoint_accepts_use_market_data_flag_without_forcing_it():
    response = client.post(
        "/simulate",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "save_json": False,
            "use_market_data": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "market_metrics" in data
    assert data["market_metrics"] is None
