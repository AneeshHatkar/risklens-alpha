from __future__ import annotations

from backend.app.schemas import Portfolio
from backend.app.services.market_data_loader import load_price_history
from backend.app.utils.finance_math import (
    annualized_volatility,
    average_pairwise_correlation,
    beta,
    cumulative_return,
    max_drawdown,
    portfolio_volatility,
)


def compute_market_metrics(
    portfolio: Portfolio,
    start: str = "2023-01-01",
    end: str | None = None,
    benchmark: str = "SPY",
) -> dict:
    tickers = [holding.ticker for holding in portfolio.holdings]

    if benchmark not in tickers:
        tickers.append(benchmark)

    market_data = load_price_history(tickers=tickers, start=start, end=end)

    weights = {holding.ticker: holding.weight for holding in portfolio.holdings}
    prices = market_data.prices
    returns = market_data.returns

    benchmark_returns = returns[benchmark] if benchmark in returns.columns else None

    asset_metrics = {}

    for ticker in [holding.ticker for holding in portfolio.holdings]:
        if ticker not in prices.columns or ticker not in returns.columns:
            asset_metrics[ticker] = {
                "available": False,
                "volatility": 0.0,
                "beta": 0.0,
                "max_drawdown": 0.0,
                "cumulative_return": 0.0,
            }
            continue

        asset_metrics[ticker] = {
            "available": True,
            "volatility": round(annualized_volatility(returns[ticker]), 4),
            "beta": round(beta(returns[ticker], benchmark_returns), 4) if benchmark_returns is not None else 0.0,
            "max_drawdown": round(max_drawdown(prices[ticker]), 4),
            "cumulative_return": round(cumulative_return(prices[ticker]), 4),
        }

    portfolio_return_series = returns[[ticker for ticker in weights if ticker in returns.columns]]
    portfolio_metrics = {
        "portfolio_volatility": round(portfolio_volatility(portfolio_return_series, weights), 4),
        "average_pairwise_correlation": round(
            average_pairwise_correlation(portfolio_return_series),
            4,
        ),
        "benchmark": benchmark,
        "start": start,
        "end": end,
        "missing_tickers": market_data.missing_tickers,
        "warnings": market_data.warnings,
        "used_cache": market_data.used_cache,
        "cache_path": market_data.cache_path,
    }

    return {
        "portfolio_metrics": portfolio_metrics,
        "asset_metrics": asset_metrics,
    }
