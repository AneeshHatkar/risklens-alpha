from backend.app.main import load_sample_portfolio
from backend.app.services.market_metrics import compute_market_metrics
from backend.app.services.portfolio_parser import normalize_portfolio


def main():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)

    metrics = compute_market_metrics(
        portfolio=portfolio,
        start="2024-01-01",
        benchmark="SPY",
    )

    print("\nRiskLens Alpha Market Metrics Check")
    print("=" * 48)
    print("Portfolio:", portfolio.name)

    portfolio_metrics = metrics["portfolio_metrics"]
    print("\nPortfolio Metrics:")
    for key, value in portfolio_metrics.items():
        print(f"- {key}: {value}")

    print("\nAsset Metrics:")
    for ticker, values in metrics["asset_metrics"].items():
        print(f"\n{ticker}")
        for key, value in values.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
