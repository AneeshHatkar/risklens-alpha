from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.schemas import Holding, PortfolioCreateRequest
from backend.app.services.alert_engine import check_alerts_for_portfolios
from backend.app.services.alert_repository import (
    alert_to_dict,
    create_alert,
    list_alerts,
    mark_alert_read,
)
from backend.app.services.portfolio_repository import create_portfolio


def make_test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionTesting()


def test_create_list_and_mark_alert_read():
    db = make_test_db()

    alert = create_alert(
        db=db,
        portfolio_id=1,
        alert_type="risk_score_threshold",
        severity="high",
        title="Risk score crossed threshold",
        message="Test alert message.",
        value=80,
        threshold=75,
    )

    alerts = list_alerts(db)

    assert len(alerts) == 1
    assert alerts[0].id == alert.id

    marked = mark_alert_read(db, alert.id)

    assert marked is not None
    assert marked.is_read is True

    data = alert_to_dict(marked)

    assert data["is_read"] is True
    assert data["severity"] == "high"

    db.close()


def test_alert_engine_creates_alerts_for_high_thresholds():
    db = make_test_db()

    create_portfolio(
        db,
        PortfolioCreateRequest(
            name="Alert Test Portfolio",
            holdings=[
                Holding(ticker="NVDA", weight=0.35),
                Holding(ticker="MSFT", weight=0.25),
                Holding(ticker="AAPL", weight=0.20),
                Holding(ticker="SPY", weight=0.20),
            ],
        ),
    )

    result = check_alerts_for_portfolios(
        db=db,
        risk_threshold=60,
        hidden_concentration_threshold=70,
        volatility_threshold=0.10,
        correlation_threshold=0.10,
    )

    assert result["portfolio_count"] == 1
    assert result["created_alert_count"] >= 1

    alerts = list_alerts(db)

    assert len(alerts) >= 1

    db.close()


def test_create_alert_if_missing_prevents_duplicate_unread_alerts():
    from backend.app.services.alert_repository import create_alert_if_missing

    db = make_test_db()

    first, first_created = create_alert_if_missing(
        db=db,
        portfolio_id=1,
        alert_type="hidden_concentration_threshold",
        severity="high",
        title="Hidden concentration crossed 80",
        message="Test alert.",
        scenario_id="ai_capex_slowdown",
        value=81,
        threshold=80,
    )

    second, second_created = create_alert_if_missing(
        db=db,
        portfolio_id=1,
        alert_type="hidden_concentration_threshold",
        severity="high",
        title="Hidden concentration crossed 80",
        message="Test alert.",
        scenario_id="ai_capex_slowdown",
        value=81,
        threshold=80,
    )

    alerts = list_alerts(db)

    assert first.id == second.id
    assert first_created is True
    assert second_created is False
    assert len(alerts) == 1

    db.close()
