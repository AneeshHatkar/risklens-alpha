from backend.app.main import load_sample_portfolio
from backend.app.services.benchmark_comparison import (
    compare_portfolio_to_benchmarks,
    list_benchmarks,
)
from backend.app.services.portfolio_parser import normalize_portfolio


def test_list_benchmarks_contains_common_etfs():
    benchmarks = list_benchmarks()

    assert "SPY" in benchmarks
    assert "QQQ" in benchmarks
    assert "SMH" in benchmarks


def test_benchmark_comparison_returns_expected_shape():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)

    result = compare_portfolio_to_benchmarks(
        portfolio=portfolio,
        benchmark_tickers=["SPY", "QQQ"],
        start="2024-01-01",
        use_cache=True,
    )

    assert result["portfolio_name"] == "AI Growth Sample Portfolio"
    assert "portfolio_metrics" in result
    assert "benchmarks" in result
    assert len(result["benchmarks"]) == 2
    assert "disclaimer" in result


def test_benchmark_comparison_contains_relative_metrics():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)

    result = compare_portfolio_to_benchmarks(
        portfolio=portfolio,
        benchmark_tickers=["SPY"],
        start="2024-01-01",
        use_cache=True,
    )

    comparison = result["benchmarks"][0]

    assert comparison["benchmark"] == "SPY"

    if comparison["available"]:
        assert "relative" in comparison
        assert "beta_to_benchmark" in comparison["relative"]
        assert "correlation_to_benchmark" in comparison["relative"]
        assert "interpretation" in comparison
