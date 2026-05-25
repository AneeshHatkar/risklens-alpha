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


def test_alert_jobs_status_endpoint_exists():
    response = client.post("/jobs/run-alert-check")

    assert response.status_code == 200
    data = response.json()

    assert "job_name" in data
    assert data["job_name"] == "alert_check"


def test_recalculate_portfolio_weights_endpoint():
    response = client.post(
        "/portfolio/recalculate-weights",
        json={
            "name": "API Live Weight Portfolio",
            "holdings": [
                {"ticker": "NVDA", "shares": 1},
                {"ticker": "MSFT", "shares": 1}
            ],
            "use_cache": True
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_market_value"] > 0
    assert len(data["holdings"]) == 2
    assert "normalized_portfolio" in data


def test_narrative_classifier_metrics_endpoint():
    response = client.get("/ml/narratives/metrics")

    assert response.status_code in {200, 503}

    if response.status_code == 200:
        data = response.json()
        assert "accuracy" in data
        assert "macro_f1" in data


def test_narrative_classifier_endpoint():
    response = client.post(
        "/ml/narratives/classify",
        json={
            "title": "Chip stocks fall after new export restrictions",
            "summary": "AI accelerator makers declined on China sales concerns.",
            "top_k": 3
        },
    )

    assert response.status_code in {200, 503}

    if response.status_code == 200:
        data = response.json()
        assert "predicted_label" in data
        assert "confidence" in data
        assert "top_labels" in data


def test_news_extract_narratives_endpoint():
    response = client.post(
        "/news/extract-narratives",
        json={
            "articles": [
                {
                    "title": "NVDA falls after China chip export restrictions",
                    "summary": "Investors worry AI accelerator shipments could be limited.",
                    "tickers": ["NVDA"]
                }
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 1
    assert "narratives" in data
    assert "narrative" in data["narratives"][0]
    assert "affected_factors" in data["narratives"][0]


def test_dynamic_factor_update_endpoint():
    response = client.post(
        "/factors/dynamic-update",
        json={
            "articles": [
                {
                    "title": "NVDA falls after China chip export restrictions",
                    "summary": "Investors worry AI accelerator shipments could be limited.",
                    "tickers": ["NVDA"]
                }
            ],
            "tickers": ["NVDA", "AMD"]
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["narrative_count"] == 1
    assert "ticker_updates" in data
    assert "NVDA" in data["ticker_updates"]


def test_simulate_endpoint_includes_agent_disagreement():
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

    assert "agent_disagreement" in data
    assert data["agent_disagreement"] is not None
    assert "score" in data["agent_disagreement"]


def test_risk_calibrator_metrics_endpoint():
    response = client.get("/ml/risk-calibrator/metrics")

    assert response.status_code in {200, 503}

    if response.status_code == 200:
        data = response.json()
        assert "score_model" in data
        assert "level_model" in data


def test_risk_calibrate_endpoint():
    response = client.post(
        "/ml/risk-calibrate",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "use_market_data": False
        },
    )

    assert response.status_code in {200, 503}

    if response.status_code == 200:
        data = response.json()
        assert "calibrated_score" in data
        assert "calibrated_level" in data
        assert "severe_probability" in data


def test_simulate_with_news_endpoint():
    response = client.post(
        "/simulate-with-news",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "use_market_data": False,
            "run_ml_calibration": False,
            "articles": [
                {
                    "title": "NVDA falls after China chip export restrictions",
                    "summary": "Investors worry AI accelerator shipments could be limited.",
                    "tickers": ["NVDA"]
                }
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["news_adjusted"] is True
    assert "result" in data
    assert "dynamic_factor_update" in data
    assert data["dynamic_factor_update"]["narrative_count"] == 1


def test_simulate_with_news_endpoint():
    response = client.post(
        "/simulate-with-news",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "use_market_data": False,
            "run_ml_calibration": False,
            "articles": [
                {
                    "title": "NVDA falls after China chip export restrictions",
                    "summary": "Investors worry AI accelerator shipments could be limited.",
                    "tickers": ["NVDA"]
                }
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["news_adjusted"] is True
    assert "result" in data
    assert "dynamic_factor_update" in data
    assert data["dynamic_factor_update"]["narrative_count"] == 1
