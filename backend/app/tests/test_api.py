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


def test_compare_scenarios_endpoint_returns_ranked_results():
    response = client.post(
        "/simulate/compare",
        json={
            "portfolio_id": "ai_growth_sample",
            "use_market_data": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 5
    assert data[0]["vulnerability_score"] >= data[-1]["vulnerability_score"]
    assert "scenario_name" in data[0]


def test_what_if_endpoint_returns_delta():
    response = client.post(
        "/simulate/what-if",
        json={
            "base_portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "use_market_data": False,
            "what_if_holdings": [
                {"ticker": "NVDA", "weight": 0.20},
                {"ticker": "MSFT", "weight": 0.25},
                {"ticker": "AAPL", "weight": 0.25},
                {"ticker": "SPY", "weight": 0.30}
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "base" in data
    assert "what_if" in data
    assert "score_delta" in data
    assert "safety_note" in data


def test_asset_search_endpoint_returns_results():
    response = client.get("/assets/search?query=NVDA")

    assert response.status_code == 200
    data = response.json()

    assert any(item["ticker"] == "NVDA" for item in data)


def test_asset_detail_endpoint_returns_profile_without_market_data():
    response = client.get("/assets/NVDA?use_market_data=false")

    assert response.status_code == 200
    data = response.json()

    assert data["ticker"] == "NVDA"
    assert data["name"] == "NVIDIA Corporation"
    assert data["market_metrics"] is None
    assert len(data["factor_exposures"]) > 0


def test_config_status_endpoint_is_safe():
    response = client.get("/config/status")

    assert response.status_code == 200
    data = response.json()

    assert data["app_name"] == "RiskLens Alpha"
    assert "configured_optional_providers" in data
    assert "api_key" not in str(data).lower()


def test_simulate_endpoint_includes_evidence_items():
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

    assert "evidence_items" in data
    assert len(data["evidence_items"]) > 0


def test_generate_sample_report_endpoint():
    response = client.post(
        "/reports/sample",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "save_json": False,
            "use_market_data": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["report_type"] == "html"
    assert data["vulnerability_score"] >= 60
    assert data["path"].endswith(".html")


def test_generate_sample_pdf_report_endpoint_handles_browser_availability():
    response = client.post(
        "/reports/sample/pdf",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "save_json": False,
            "use_market_data": False,
        },
    )

    assert response.status_code in {200, 503}

    if response.status_code == 200:
        data = response.json()
        assert data["report_type"] == "pdf"
        assert data["path"].endswith(".pdf")
    else:
        assert "browser" in response.json()["detail"].lower()


def test_evaluate_endpoint_returns_suite_result():
    response = client.get("/evaluate?use_market_data=false")

    assert response.status_code == 200
    data = response.json()

    assert data["suite_name"] == "RiskLens Alpha Evaluation Suite"
    assert data["case_count"] >= 3
    assert 0 <= data["overall_score"] <= 100
    assert "results" in data


def test_historical_shocks_endpoint_returns_catalog():
    response = client.get("/historical-shocks")

    assert response.status_code == 200
    data = response.json()

    assert "covid_crash_2020" in data
    assert "rate_shock_2022" in data


def test_historical_replay_endpoint_returns_result():
    response = client.post(
        "/historical-replay",
        json={
            "portfolio_id": "ai_growth_sample",
            "shock_id": "rate_shock_2022",
            "use_cache": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["shock_id"] == "rate_shock_2022"
    assert "portfolio_metrics" in data
    assert "asset_impacts" in data


def test_benchmarks_endpoint_returns_catalog():
    response = client.get("/benchmarks")

    assert response.status_code == 200
    data = response.json()

    assert "SPY" in data
    assert "QQQ" in data


def test_benchmark_compare_endpoint_returns_result():
    response = client.post(
        "/benchmarks/compare",
        json={
            "portfolio_id": "ai_growth_sample",
            "benchmark_tickers": ["SPY", "QQQ"],
            "start": "2024-01-01",
            "end": None,
            "use_cache": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "portfolio_metrics" in data
    assert "benchmarks" in data
    assert len(data["benchmarks"]) == 2


def test_jobs_status_endpoint_returns_shape():
    response = client.get("/jobs/status")

    assert response.status_code == 200
    data = response.json()

    assert "running" in data
    assert "jobs" in data


def test_jobs_status_endpoint_returns_shape():
    response = client.get("/jobs/status")

    assert response.status_code == 200
    data = response.json()

    assert "running" in data
    assert "jobs" in data
