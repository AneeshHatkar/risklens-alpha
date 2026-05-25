from backend.app.services.custom_portfolio_builder import (
    build_custom_portfolio,
    normalize_custom_holdings,
)


def test_normalize_custom_weight_holdings():
    holdings = normalize_custom_holdings(
        [
            {"ticker": "nvda", "weight": 40},
            {"ticker": "msft", "weight": 30},
            {"ticker": "spy", "weight": 30},
        ]
    )

    assert holdings[0].ticker == "NVDA"
    assert round(sum(item.weight for item in holdings), 4) == 1.0


def test_normalize_custom_share_holdings_equal_weights():
    holdings = normalize_custom_holdings(
        [
            {"ticker": "NVDA", "shares": 10},
            {"ticker": "MSFT", "shares": 5},
        ]
    )

    assert len(holdings) == 2
    assert holdings[0].weight == 0.5


def test_build_custom_portfolio():
    portfolio = build_custom_portfolio(
        name="My Test Portfolio",
        holdings=[
            {"ticker": "NVDA", "weight": 0.6},
            {"ticker": "SPY", "weight": 0.4},
        ],
    )

    assert portfolio.name == "My Test Portfolio"
    assert len(portfolio.holdings) == 2
