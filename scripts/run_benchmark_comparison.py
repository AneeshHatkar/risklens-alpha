import json
from pathlib import Path

from backend.app.main import load_sample_portfolio
from backend.app.services.benchmark_comparison import compare_portfolio_to_benchmarks
from backend.app.services.portfolio_parser import normalize_portfolio


def main():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)

    result = compare_portfolio_to_benchmarks(
        portfolio=portfolio,
        benchmark_tickers=["SPY", "QQQ", "SMH", "XLK"],
        start="2024-01-01",
        use_cache=True,
    )

    output_path = Path("reports/json/benchmark_comparison.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\nRiskLens Alpha Benchmark Comparison")
    print("=" * 56)
    print(f"Portfolio: {result['portfolio_name']}")
    print(f"Window: {result['start']} to {result['end']}")

    print("\nPortfolio Metrics:")
    for key, value in result["portfolio_metrics"].items():
        print(f"- {key}: {value}")

    print("\nBenchmark Comparisons:")
    for item in result["benchmarks"]:
        print(f"\n{item['benchmark']} — {item['name']}")
        if not item["available"]:
            print(f"- unavailable: {item.get('warning')}")
            continue

        print(f"- benchmark_return: {item['benchmark_metrics']['cumulative_return']}")
        print(f"- benchmark_volatility: {item['benchmark_metrics']['volatility']}")
        print(f"- benchmark_max_drawdown: {item['benchmark_metrics']['max_drawdown']}")
        print(f"- beta_to_benchmark: {item['relative']['beta_to_benchmark']}")
        print(f"- correlation_to_benchmark: {item['relative']['correlation_to_benchmark']}")
        print(f"- interpretation: {item['interpretation']}")

    print(f"\nSaved benchmark comparison to: {output_path}")


if __name__ == "__main__":
    main()
