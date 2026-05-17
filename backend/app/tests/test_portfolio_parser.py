import pytest

from backend.app.services.portfolio_parser import normalize_portfolio


def test_normalize_portfolio_uppercases_tickers():
    raw = {
        "name": "Test Portfolio",
        "holdings": [
            {"ticker": " nvda ", "weight": 0.5},
            {"ticker": "msft", "weight": 0.5},
        ],
    }

    portfolio = normalize_portfolio(raw)

    assert portfolio.holdings[0].ticker == "NVDA"
    assert portfolio.holdings[1].ticker == "MSFT"


def test_normalize_portfolio_normalizes_weights_to_one():
    raw = {
        "name": "Test Portfolio",
        "holdings": [
            {"ticker": "NVDA", "weight": 35},
            {"ticker": "MSFT", "weight": 25},
            {"ticker": "AAPL", "weight": 20},
            {"ticker": "SPY", "weight": 20},
        ],
    }

    portfolio = normalize_portfolio(raw)
    total_weight = sum(holding.weight for holding in portfolio.holdings)

    assert abs(total_weight - 1.0) < 0.001
    assert round(portfolio.holdings[0].weight, 2) == 0.35


def test_normalize_portfolio_rejects_duplicate_tickers():
    raw = {
        "name": "Bad Portfolio",
        "holdings": [
            {"ticker": "NVDA", "weight": 0.5},
            {"ticker": "nvda", "weight": 0.5},
        ],
    }

    with pytest.raises(ValueError, match="Duplicate tickers"):
        normalize_portfolio(raw)


def test_normalize_portfolio_rejects_zero_total_weight():
    raw = {
        "name": "Bad Portfolio",
        "holdings": [
            {"ticker": "NVDA", "weight": 0},
            {"ticker": "MSFT", "weight": 0},
        ],
    }

    with pytest.raises(ValueError, match="greater than 0"):
        normalize_portfolio(raw)
