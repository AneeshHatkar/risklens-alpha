from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.main import run_simulation
from backend.app.schemas import Holding, PortfolioCreateRequest
from backend.app.services.job_manager import get_scheduler_status
from backend.app.services.portfolio_repository import create_portfolio
from backend.app.services.timeline_repository import (
    list_timeline_points,
    save_timeline_point,
    timeline_point_to_dict,
)


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


def test_save_and_list_timeline_points():
    db = make_test_db()

    portfolio = create_portfolio(
        db,
        PortfolioCreateRequest(
            name="Timeline Test Portfolio",
            holdings=[
                Holding(ticker="NVDA", weight=0.5),
                Holding(ticker="SPY", weight=0.5),
            ],
        ),
    )

    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    point = save_timeline_point(
        db=db,
        portfolio_id=portfolio.id,
        scenario_id="ai_capex_slowdown",
        result=result,
        source="test",
    )

    points = list_timeline_points(db, portfolio_id=portfolio.id)

    assert point.id is not None
    assert len(points) == 1

    data = timeline_point_to_dict(points[0])

    assert data["portfolio_id"] == portfolio.id
    assert data["scenario_id"] == "ai_capex_slowdown"
    assert data["source"] == "test"

    db.close()


def test_scheduler_status_shape():
    status = get_scheduler_status()

    assert "running" in status
    assert "jobs" in status
    assert isinstance(status["jobs"], list)
