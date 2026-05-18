from __future__ import annotations

from backend.app.schemas import Portfolio
from backend.app.services.market_data_loader import load_price_history
from backend.app.utils.finance_math import (
    annualized_volatility,
    beta,
    cumulative_return,
    max_drawdown,
    portfolio_returns,
)


BENCHMARKS = {
    "SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "category": "Broad U.S. large-cap equities",
    },
    "QQQ": {
        "name": "Invesco QQQ Trust",
        "category": "NASDAQ-100 / growth-heavy technology",
    },
    "SMH": {
        "name": "VanEck Semiconductor ETF",
        "category": "Semiconductors",
    },
    "XLK": {
        "name": "Technology Select Sector SPDR Fund",
        "category": "U.S. technology sector",
    },
    "XLF": {
        "name": "Financial Select Sector SPDR Fund",
        "category": "U.S. financial sector",
    },
    "XLE": {
        "name": "Energy Select Sector SPDR Fund",
        "category": "U.S. energy sector",
    },
    "IWM": {
        "name": "iShares Russell 2000 ETF",
        "category": "U.S. small-cap equities",
    },
    "VTI": {
        "name": "Vanguard Total Stock Market ETF",
        "category": "Total U.S. equity market",
    },
    "DIA": {
        "name": "SPDR Dow Jones Industrial Average ETF Trust",
        "category": "Dow Jones Industrial Average",
    },
}


def list_benchmarks() -> dict:
    return BENCHMARKS


def compare_portfolio_to_benchmarks(
    portfolio: Portfolio,
    benchmark_tickers: list[str] | None = None,
    start: str = "2024-01-01",
    end: str | None = None,
    use_cache: bool = True,
) -> dict:
    if benchmark_tickers is None:
        benchmark_tickers = ["SPY", "QQQ", "SMH", "XLK"]

    benchmarks = [ticker.upper() for ticker in benchmark_tickers]
    portfolio_tickers = [holding.ticker for holding in portfolio.holdings]

    all_tickers = list(dict.fromkeys(portfolio_tickers + benchmarks))

    market_data = load_price_history(
        tickers=all_tickers,
        start=start,
        end=end,
        use_cache=use_cache,
    )

    prices = market_data.prices
    returns = market_data.returns

    weights = {
        holding.ticker: holding.weight
        for holding in portfolio.holdings
        if holding.ticker in returns.columns
    }

    p_returns = portfolio_returns(returns, weights)
    p_curve = (1 + p_returns).cumprod() if not p_returns.empty else p_returns

    portfolio_metrics = {
        "cumulative_return": round(float((1 + p_returns).prod() - 1), 4) if not p_returns.empty else 0.0,
        "volatility": round(annualized_volatility(p_returns), 4),
        "max_drawdown": round(max_drawdown(p_curve), 4) if not p_curve.empty else 0.0,
    }

    comparisons = []

    for benchmark in benchmarks:
        if benchmark not in prices.columns or benchmark not in returns.columns:
            comparisons.append(
                {
                    "benchmark": benchmark,
                    "name": BENCHMARKS.get(benchmark, {}).get("name", benchmark),
                    "category": BENCHMARKS.get(benchmark, {}).get("category", "Unknown"),
                    "available": False,
                    "warning": "Benchmark price data unavailable.",
                }
            )
            continue

        b_returns = returns[benchmark]
        benchmark_metrics = {
            "cumulative_return": round(cumulative_return(prices[benchmark]), 4),
            "volatility": round(annualized_volatility(b_returns), 4),
            "max_drawdown": round(max_drawdown(prices[benchmark]), 4),
        }

        relative = {
            "return_difference": round(
                portfolio_metrics["cumulative_return"] - benchmark_metrics["cumulative_return"],
                4,
            ),
            "volatility_difference": round(
                portfolio_metrics["volatility"] - benchmark_metrics["volatility"],
                4,
            ),
            "drawdown_difference": round(
                portfolio_metrics["max_drawdown"] - benchmark_metrics["max_drawdown"],
                4,
            ),
            "beta_to_benchmark": round(beta(p_returns, b_returns), 4) if not p_returns.empty else 0.0,
            "correlation_to_benchmark": round(
                p_returns.corr(b_returns),
                4,
            ) if not p_returns.empty else 0.0,
        }

        comparisons.append(
            {
                "benchmark": benchmark,
                "name": BENCHMARKS.get(benchmark, {}).get("name", benchmark),
                "category": BENCHMARKS.get(benchmark, {}).get("category", "Unknown"),
                "available": True,
                "benchmark_metrics": benchmark_metrics,
                "relative": relative,
                "interpretation": build_benchmark_interpretation(
                    benchmark=benchmark,
                    portfolio_metrics=portfolio_metrics,
                    benchmark_metrics=benchmark_metrics,
                    relative=relative,
                ),
            }
        )

    return {
        "portfolio_name": portfolio.name,
        "start": start,
        "end": end,
        "portfolio_metrics": portfolio_metrics,
        "benchmarks": comparisons,
        "market_data": {
            "missing_tickers": market_data.missing_tickers,
            "warnings": market_data.warnings,
            "used_cache": market_data.used_cache,
            "cache_path": market_data.cache_path,
        },
        "disclaimer": (
            "Benchmark comparison is educational analysis only. It is not financial advice "
            "and does not recommend buying or selling securities."
        ),
    }


def build_benchmark_interpretation(
    benchmark: str,
    portfolio_metrics: dict,
    benchmark_metrics: dict,
    relative: dict,
) -> str:
    parts = []

    if relative["volatility_difference"] > 0.03:
        parts.append(f"The portfolio was more volatile than {benchmark}.")
    elif relative["volatility_difference"] < -0.03:
        parts.append(f"The portfolio was less volatile than {benchmark}.")
    else:
        parts.append(f"The portfolio had similar volatility to {benchmark}.")

    if relative["drawdown_difference"] < -0.03:
        parts.append(f"The portfolio had a deeper drawdown than {benchmark}.")
    elif relative["drawdown_difference"] > 0.03:
        parts.append(f"The portfolio had a smaller drawdown than {benchmark}.")
    else:
        parts.append(f"The portfolio had a similar drawdown to {benchmark}.")

    if relative["correlation_to_benchmark"] >= 0.85:
        parts.append(f"The portfolio was highly correlated with {benchmark}.")
    elif relative["correlation_to_benchmark"] >= 0.60:
        parts.append(f"The portfolio was moderately correlated with {benchmark}.")
    else:
        parts.append(f"The portfolio had relatively low correlation with {benchmark}.")

    return " ".join(parts)
