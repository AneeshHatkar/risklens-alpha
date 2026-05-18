from backend.app.services.asset_explorer import find_assets, get_asset_profile


def main():
    print("\nRiskLens Alpha Asset Search")
    print("=" * 48)

    results = find_assets("NVDA")

    for item in results:
        print(f"- {item.ticker}: {item.name} | {item.sector} | {item.industry}")

    print("\nRiskLens Alpha Asset Profile")
    print("=" * 48)

    profile = get_asset_profile("NVDA", use_market_data=True)

    print("Ticker:", profile.ticker)
    print("Name:", profile.name)
    print("Sector:", profile.sector)
    print("Industry:", profile.industry)
    print("Related scenarios:", ", ".join(profile.related_scenarios))

    print("\nTop Factor Exposures:")
    for exposure in profile.factor_exposures[:5]:
        print(f"- {exposure.factor}: score={exposure.score}, confidence={exposure.confidence}")

    if profile.market_metrics:
        print("\nMarket Metrics:")
        asset_metrics = profile.market_metrics["asset_metrics"].get(profile.ticker, {})
        for key, value in asset_metrics.items():
            print(f"- {key}: {value}")

    if profile.warnings:
        print("\nWarnings:")
        for warning in profile.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
