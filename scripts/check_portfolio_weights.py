from backend.app.schemas import LiveWeightHoldingInput, LiveWeightRequest
from backend.app.services.portfolio_weight_engine import recalculate_weights_from_shares


def main():
    request = LiveWeightRequest(
        name="Live Weight Demo Portfolio",
        holdings=[
            LiveWeightHoldingInput(ticker="NVDA", shares=10),
            LiveWeightHoldingInput(ticker="MSFT", shares=5),
            LiveWeightHoldingInput(ticker="AAPL", shares=8),
            LiveWeightHoldingInput(ticker="SPY", shares=3),
        ],
        use_cache=True,
    )

    result = recalculate_weights_from_shares(request)

    print("\nRiskLens Alpha Live Portfolio Weights")
    print("=" * 56)
    print(f"Portfolio: {result.name}")
    print(f"Total market value: {result.total_market_value}")

    print("\nHoldings:")
    for holding in result.holdings:
        print(
            f"- {holding.ticker}: shares={holding.shares}, "
            f"price={holding.latest_price}, market_value={holding.market_value}, "
            f"weight={holding.weight}"
        )

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
