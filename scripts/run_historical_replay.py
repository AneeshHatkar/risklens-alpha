import json
from pathlib import Path

from backend.app.main import load_sample_portfolio
from backend.app.services.historical_shocks import replay_historical_shock
from backend.app.services.portfolio_parser import normalize_portfolio


def main():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)

    result = replay_historical_shock(
        portfolio=portfolio,
        shock_id="rate_shock_2022",
        use_cache=True,
    )

    output_path = Path("reports/json/historical_replay.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\nRiskLens Alpha Historical Shock Replay")
    print("=" * 56)
    print(f"Portfolio: {result['portfolio_name']}")
    print(f"Shock: {result['shock_name']}")
    print(f"Window: {result['start']} to {result['end']}")
    print(f"Benchmark: {result['benchmark']}")
    print("\nPortfolio Metrics:")
    for key, value in result["portfolio_metrics"].items():
        print(f"- {key}: {value}")

    if result["benchmark_metrics"]:
        print("\nBenchmark Metrics:")
        for key, value in result["benchmark_metrics"].items():
            print(f"- {key}: {value}")

    print("\nWorst Contributors:")
    for item in result["worst_contributors"]:
        print(
            f"- {item['ticker']}: cumulative_return={item['cumulative_return']}, "
            f"contribution_estimate={item['contribution_estimate']}"
        )

    print("\nSummary:")
    print(result["summary"])
    print(f"\nSaved replay result to: {output_path}")


if __name__ == "__main__":
    main()
