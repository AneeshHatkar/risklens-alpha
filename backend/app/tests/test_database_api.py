from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api import app
from backend.app.database import Base, get_db


def make_test_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    # Import models so SQLAlchemy registers tables before create_all.
    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    return client


def clear_overrides():
    app.dependency_overrides.clear()


def test_create_and_list_database_portfolio():
    client = make_test_client()

    response = client.post(
        "/db/portfolios",
        json={
            "name": "API Test Portfolio",
            "owner_label": "test",
            "holdings": [
                {"ticker": "NVDA", "weight": 0.6},
                {"ticker": "MSFT", "weight": 0.4},
            ],
        },
    )

    assert response.status_code == 200
    created = response.json()

    assert created["name"] == "API Test Portfolio"
    assert created["holding_count"] == 2

    list_response = client.get("/db/portfolios")

    assert list_response.status_code == 200
    portfolios = list_response.json()

    assert len(portfolios) == 1
    assert portfolios[0]["name"] == "API Test Portfolio"

    clear_overrides()


def test_get_database_portfolio_detail():
    client = make_test_client()

    create_response = client.post(
        "/db/portfolios",
        json={
            "name": "Detail Test Portfolio",
            "owner_label": "test",
            "holdings": [
                {"ticker": "AAPL", "weight": 0.5},
                {"ticker": "SPY", "weight": 0.5},
            ],
        },
    )

    portfolio_id = create_response.json()["id"]

    detail_response = client.get(f"/db/portfolios/{portfolio_id}")

    assert detail_response.status_code == 200
    detail = detail_response.json()

    assert detail["name"] == "Detail Test Portfolio"
    assert len(detail["holdings"]) == 2
    assert detail["holdings"][0]["ticker"] == "AAPL"

    clear_overrides()


def test_delete_database_portfolio():
    client = make_test_client()

    create_response = client.post(
        "/db/portfolios",
        json={
            "name": "Delete Test Portfolio",
            "owner_label": "test",
            "holdings": [
                {"ticker": "SPY", "weight": 1.0},
            ],
        },
    )

    portfolio_id = create_response.json()["id"]

    delete_response = client.delete(f"/db/portfolios/{portfolio_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    missing_response = client.get(f"/db/portfolios/{portfolio_id}")

    assert missing_response.status_code == 404

    clear_overrides()


def test_database_portfolio_simulation_saves_history():
    client = make_test_client()

    create_response = client.post(
        "/db/portfolios",
        json={
            "name": "Simulation Test Portfolio",
            "owner_label": "test",
            "holdings": [
                {"ticker": "NVDA", "weight": 0.35},
                {"ticker": "MSFT", "weight": 0.25},
                {"ticker": "AAPL", "weight": 0.20},
                {"ticker": "SPY", "weight": 0.20},
            ],
        },
    )

    portfolio_id = create_response.json()["id"]

    simulate_response = client.post(
        f"/db/portfolios/{portfolio_id}/simulate",
        json={
            "portfolio_id": "ai_growth_sample",
            "scenario_id": "ai_capex_slowdown",
            "save_json": False,
            "use_market_data": False,
        },
    )

    assert simulate_response.status_code == 200
    data = simulate_response.json()

    assert "simulation_run_id" in data
    assert data["result"]["vulnerability_score"] >= 60

    history_response = client.get("/db/simulation-runs")

    assert history_response.status_code == 200
    history = history_response.json()

    assert len(history) == 1
    assert history[0]["portfolio_id"] == portfolio_id
    assert history[0]["scenario_id"] == "ai_capex_slowdown"

    clear_overrides()


def test_get_database_simulation_run_detail():
    client = make_test_client()

    create_response = client.post(
        "/db/portfolios",
        json={
            "name": "Run Detail Portfolio",
            "owner_label": "test",
            "holdings": [
                {"ticker": "NVDA", "weight": 0.5},
                {"ticker": "SPY", "weight": 0.5},
            ],
        },
    )

    portfolio_id = create_response.json()["id"]

    simulate_response = client.post(
        f"/db/portfolios/{portfolio_id}/simulate",
        json={
            "scenario_id": "ai_capex_slowdown",
            "use_market_data": False,
            "save_json": False,
        },
    )

    run_id = simulate_response.json()["simulation_run_id"]

    detail_response = client.get(f"/db/simulation-runs/{run_id}")

    assert detail_response.status_code == 200
    detail = detail_response.json()

    assert detail["id"] == run_id
    assert detail["result"]["scenario"]["name"] == "AI Infrastructure Spending Slowdown"

    clear_overrides()


def test_database_watchlist_endpoints():
    client = make_test_client()

    add_response = client.post(
        "/db/watchlist",
        json={
            "ticker": "nvda",
            "notes": "Track AI infrastructure exposure",
        },
    )

    assert add_response.status_code == 200
    item = add_response.json()

    assert item["ticker"] == "NVDA"
    assert item["name"] == "NVIDIA Corporation"

    list_response = client.get("/db/watchlist")

    assert list_response.status_code == 200
    items = list_response.json()

    assert len(items) == 1
    assert items[0]["ticker"] == "NVDA"

    delete_response = client.delete(f"/db/watchlist/{item['id']}")

    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    clear_overrides()


def test_database_simulation_creates_timeline_point():
    client = make_test_client()

    create_response = client.post(
        "/db/portfolios",
        json={
            "name": "Timeline API Portfolio",
            "owner_label": "test",
            "holdings": [
                {"ticker": "NVDA", "weight": 0.5},
                {"ticker": "SPY", "weight": 0.5},
            ],
        },
    )

    portfolio_id = create_response.json()["id"]

    simulate_response = client.post(
        f"/db/portfolios/{portfolio_id}/simulate",
        json={
            "scenario_id": "ai_capex_slowdown",
            "use_market_data": False,
            "save_json": False,
        },
    )

    assert simulate_response.status_code == 200
    assert "timeline_point_id" in simulate_response.json()

    timeline_response = client.get(f"/db/portfolios/{portfolio_id}/timeline")

    assert timeline_response.status_code == 200
    timeline = timeline_response.json()

    assert len(timeline) == 1
    assert timeline[0]["scenario_id"] == "ai_capex_slowdown"

    clear_overrides()


def test_timeline_anomalies_endpoint_returns_shape():
    client = make_test_client()

    create_response = client.post(
        "/db/portfolios",
        json={
            "name": "Anomaly API Portfolio",
            "owner_label": "test",
            "holdings": [
                {"ticker": "NVDA", "weight": 0.5},
                {"ticker": "SPY", "weight": 0.5},
            ],
        },
    )

    portfolio_id = create_response.json()["id"]

    response = client.get(f"/db/portfolios/{portfolio_id}/timeline/anomalies")

    assert response.status_code == 200
    data = response.json()

    assert "point_count" in data
    assert "anomaly_count" in data
    assert "anomalies" in data

    clear_overrides()
