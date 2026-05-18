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


HISTORICAL_SHOCKS = {
    "covid_crash_2020": {
        "name": "COVID Crash 2020",
        "start": "2020-02-19",
        "end": "2020-03-23",
        "description": "Rapid equity market drawdown during the initial COVID-19 pandemic shock.",
        "benchmark": "SPY",
        "expected_themes": [
            "liquidity shock",
            "market beta",
            "volatility expansion",
            "correlation spike",
        ],
    },
    "rate_shock_2022": {
        "name": "2022 Rate Shock / Tech Drawdown",
        "start": "2022-01-03",
        "end": "2022-10-14",
        "description": "Growth and technology drawdown during aggressive rate-hike repricing.",
        "benchmark": "QQQ",
        "expected_themes": [
            "interest rates",
            "valuation multiples",
            "growth stocks",
            "liquidity conditions",
        ],
    },
    "regional_banking_2023": {
        "name": "Regional Banking Stress 2023",
        "start": "2023-03-08",
        "end": "2023-03-24",
        "description": "Market stress around U.S. regional banking failures and financial-sector contagion concerns.",
        "benchmark": "SPY",
        "expected_themes": [
            "financial stress",
            "liquidity conditions",
            "market beta",
            "risk-off sentiment",
        ],
    },
    "inflation_oil_shock_2022": {
        "name": "Inflation and Oil Shock 2022",
        "start": "2022-02-24",
        "end": "2022-06-16",
        "description": "Inflation, commodity, and rate pressure period after Russia's invasion of Ukraine.",
        "benchmark": "SPY",
        "expected_themes": [
            "inflation pressure",
            "oil shock",
            "interest rates",
            "consumer demand",
        ],
    },
    "ai_semiconductor_pullback_2024": {
        "name": "AI/Semiconductor Pullback 2024",
        "start": "2024-07-10",
        "end": "2024-08-07",
        "description": "A recent pullback window for AI and semiconductor-linked equities.",
        "benchmark": "SMH",
        "expected_themes": [
            "AI infrastructure",
            "semiconductors",
            "valuation multiples",
            "market beta",
        ],
    },
}


def list_historical_shocks() -> dict:
    return HISTORICAL_SHOCKS


def get_historical_shock(shock_id: str) -> dict:
    if shock_id not in HISTORICAL_SHOCKS:
        valid = ", ".join(HISTORICAL_SHOCKS.keys())
        raise ValueError(f"Unknown historical shock '{shock_id}'. Valid options: {valid}")

    return HISTORICAL_SHOCKS[shock_id]


def replay_historical_shock(
    portfolio: Portfolio,
    shock_id: str,
    use_cache: bool = True,
) -> dict:
    shock = get_historical_shock(shock_id)
    benchmark = shock["benchmark"]

    tickers = [holding.ticker for holding in portfolio.holdings]

    if benchmark not in tickers:
        tickers.append(benchmark)

    market_data = load_price_history(
        tickers=tickers,
        start=shock["start"],
        end=shock["end"],
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

    benchmark_metrics = None
    if benchmark in prices.columns and benchmark in returns.columns:
        benchmark_metrics = {
            "ticker": benchmark,
            "cumulative_return": round(cumulative_return(prices[benchmark]), 4),
            "max_drawdown": round(max_drawdown(prices[benchmark]), 4),
            "volatility": round(annualized_volatility(returns[benchmark]), 4),
        }

    portfolio_metrics = {
        "cumulative_return": round(float((1 + p_returns).prod() - 1), 4) if not p_returns.empty else 0.0,
        "max_drawdown": round(max_drawdown((1 + p_returns).cumprod()), 4) if not p_returns.empty else 0.0,
        "volatility": round(annualized_volatility(p_returns), 4),
        "beta_to_benchmark": (
            round(beta(p_returns, returns[benchmark]), 4)
            if benchmark in returns.columns and not p_returns.empty
            else 0.0
        ),
    }

    asset_impacts = {}

    for holding in portfolio.holdings:
        ticker = holding.ticker

        if ticker not in prices.columns or ticker not in returns.columns:
            asset_impacts[ticker] = {
                "available": False,
                "weight": holding.weight,
                "cumulative_return": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0,
                "contribution_estimate": 0.0,
            }
            continue

        asset_return = cumulative_return(prices[ticker])
        asset_impacts[ticker] = {
            "available": True,
            "weight": holding.weight,
            "cumulative_return": round(asset_return, 4),
            "max_drawdown": round(max_drawdown(prices[ticker]), 4),
            "volatility": round(annualized_volatility(returns[ticker]), 4),
            "contribution_estimate": round(holding.weight * asset_return, 4),
        }

    ranked_impacts = sorted(
        asset_impacts.items(),
        key=lambda item: item[1]["contribution_estimate"],
    )

    worst_contributors = [
        {
            "ticker": ticker,
            **metrics,
        }
        for ticker, metrics in ranked_impacts[:5]
    ]

    return {
        "portfolio_name": portfolio.name,
        "shock_id": shock_id,
        "shock_name": shock["name"],
        "description": shock["description"],
        "start": shock["start"],
        "end": shock["end"],
        "benchmark": benchmark,
        "expected_themes": shock["expected_themes"],
        "portfolio_metrics": portfolio_metrics,
        "benchmark_metrics": benchmark_metrics,
        "asset_impacts": asset_impacts,
        "worst_contributors": worst_contributors,
        "market_data": {
            "missing_tickers": market_data.missing_tickers,
            "warnings": market_data.warnings,
            "used_cache": market_data.used_cache,
            "cache_path": market_data.cache_path,
        },
        "summary": build_historical_replay_summary(
            shock_name=shock["name"],
            portfolio_metrics=portfolio_metrics,
            benchmark_metrics=benchmark_metrics,
            benchmark=benchmark,
        ),
        "disclaimer": (
            "Historical replay is educational scenario analysis only. "
            "Past market behavior does not guarantee future results and is not financial advice."
        ),
    }


def build_historical_replay_summary(
    shock_name: str,
    portfolio_metrics: dict,
    benchmark_metrics: dict | None,
    benchmark: str,
) -> str:
    portfolio_drawdown = portfolio_metrics["max_drawdown"]
    portfolio_return = portfolio_metrics["cumulative_return"]

    if benchmark_metrics:
        benchmark_drawdown = benchmark_metrics["max_drawdown"]
        benchmark_return = benchmark_metrics["cumulative_return"]

        return (
            f"During {shock_name}, the replayed portfolio had an estimated cumulative return of "
            f"{portfolio_return:.2%} and max drawdown of {portfolio_drawdown:.2%}. "
            f"The benchmark {benchmark} had cumulative return of {benchmark_return:.2%} "
            f"and max drawdown of {benchmark_drawdown:.2%} over the same window."
        )

    return (
        f"During {shock_name}, the replayed portfolio had an estimated cumulative return of "
        f"{portfolio_return:.2%} and max drawdown of {portfolio_drawdown:.2%}."
    )
