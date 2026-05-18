from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import PortfolioModel  # noqa: F401
from backend.app.schemas import Holding, PortfolioCreateRequest
from backend.app.services.portfolio_repository import (
    create_portfolio,
    get_portfolio_by_id,
    list_portfolios,
    portfolio_detail,
)
from backend.app.services.watchlist_repository import (
    add_watchlist_item,
    list_watchlist_items,
)


def make_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionTesting()


def test_create_and_get_portfolio():
    db = make_test_db()

    request = PortfolioCreateRequest(
        name="Test Portfolio",
        holdings=[
            Holding(ticker="NVDA", weight=0.6),
            Holding(ticker="MSFT", weight=0.4),
        ],
    )

    created = create_portfolio(db, request)
    fetched = get_portfolio_by_id(db, created.id)

    assert fetched is not None
    assert fetched.name == "Test Portfolio"
    assert len(fetched.holdings) == 2

    detail = portfolio_detail(fetched)

    assert detail["name"] == "Test Portfolio"
    assert detail["holdings"][0]["ticker"] == "NVDA"

    db.close()


def test_list_portfolios():
    db = make_test_db()

    request = PortfolioCreateRequest(
        name="Portfolio One",
        holdings=[
            Holding(ticker="SPY", weight=1.0),
        ],
    )

    create_portfolio(db, request)
    portfolios = list_portfolios(db)

    assert len(portfolios) == 1
    assert portfolios[0].name == "Portfolio One"

    db.close()


def test_add_watchlist_item():
    db = make_test_db()

    item = add_watchlist_item(db, ticker="nvda")
    items = list_watchlist_items(db)

    assert item.ticker == "NVDA"
    assert len(items) == 1
    assert items[0].ticker == "NVDA"

    db.close()
