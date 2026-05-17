from __future__ import annotations

import math

import numpy as np
import pandas as pd


TRADING_DAYS = 252


def annualized_volatility(returns: pd.Series) -> float:
    clean = returns.dropna()

    if clean.empty:
        return 0.0

    return float(clean.std() * math.sqrt(TRADING_DAYS))


def max_drawdown(prices: pd.Series) -> float:
    clean = prices.dropna()

    if clean.empty:
        return 0.0

    running_max = clean.cummax()
    drawdown = (clean / running_max) - 1.0

    return float(drawdown.min())


def beta(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    combined = pd.concat([asset_returns, benchmark_returns], axis=1).dropna()

    if combined.empty or len(combined) < 2:
        return 0.0

    asset = combined.iloc[:, 0]
    benchmark = combined.iloc[:, 1]

    benchmark_variance = benchmark.var()

    if benchmark_variance == 0 or np.isnan(benchmark_variance):
        return 0.0

    covariance = asset.cov(benchmark)
    return float(covariance / benchmark_variance)


def cumulative_return(prices: pd.Series) -> float:
    clean = prices.dropna()

    if len(clean) < 2:
        return 0.0

    return float((clean.iloc[-1] / clean.iloc[0]) - 1.0)


def average_pairwise_correlation(returns: pd.DataFrame) -> float:
    clean = returns.dropna(how="all")

    if clean.empty or clean.shape[1] < 2:
        return 0.0

    corr = clean.corr()
    upper_values = []

    columns = list(corr.columns)
    for i, left in enumerate(columns):
        for right in columns[i + 1:]:
            value = corr.loc[left, right]
            if not pd.isna(value):
                upper_values.append(value)

    if not upper_values:
        return 0.0

    return float(np.mean(upper_values))


def portfolio_returns(returns: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    aligned = returns.copy()
    weighted = pd.Series(0.0, index=aligned.index)

    for ticker, weight in weights.items():
        if ticker in aligned.columns:
            weighted = weighted.add(aligned[ticker].fillna(0.0) * weight, fill_value=0.0)

    return weighted


def portfolio_volatility(returns: pd.DataFrame, weights: dict[str, float]) -> float:
    p_returns = portfolio_returns(returns, weights)
    return annualized_volatility(p_returns)


def normalize_0_1(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0

    return max(0.0, min(1.0, (value - low) / (high - low)))
