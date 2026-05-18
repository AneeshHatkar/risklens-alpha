from backend.app.schemas import LiveWeightHoldingInput, LiveWeightRequest
from backend.app.services.portfolio_weight_engine import recalculate_weights_from_shares


def test_recalculate_weights_from_shares_returns_weights():
    request = LiveWeightRequest(
        name="Test Live Weight Portfolio",
        holdings=[
            LiveWeightHoldingInput(ticker="NVDA", shares=1),
            LiveWeightHoldingInput(ticker="MSFT", shares=1),
        ],
        use_cache=True,
    )

    result = recalculate_weights_from_shares(request)

    assert result.total_market_value > 0
    assert len(result.holdings) == 2
    assert len(result.normalized_portfolio.holdings) == 2

    weights = [
        holding.weight
        for holding in result.holdings
        if holding.weight is not None
    ]

    assert abs(sum(weights) - 1.0) < 0.01


def test_recalculate_weights_normalized_portfolio_usable():
    request = LiveWeightRequest(
        name="Usable Portfolio",
        holdings=[
            LiveWeightHoldingInput(ticker="NVDA", shares=1),
            LiveWeightHoldingInput(ticker="SPY", shares=1),
        ],
        use_cache=True,
    )

    result = recalculate_weights_from_shares(request)

    assert result.normalized_portfolio.name == "Usable Portfolio"
    assert all(
        holding.weight <= 1
        for holding in result.normalized_portfolio.holdings
    )
