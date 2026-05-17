import pandas as pd

from backend.app.utils.finance_math import (
    average_pairwise_correlation,
    beta,
    cumulative_return,
    max_drawdown,
)


def test_cumulative_return():
    prices = pd.Series([100, 110, 121])

    assert round(cumulative_return(prices), 2) == 0.21


def test_max_drawdown():
    prices = pd.Series([100, 120, 90, 95])

    assert round(max_drawdown(prices), 2) == -0.25


def test_beta_positive_for_related_series():
    asset = pd.Series([0.01, 0.02, -0.01, 0.03])
    benchmark = pd.Series([0.005, 0.015, -0.005, 0.02])

    assert beta(asset, benchmark) > 0


def test_average_pairwise_correlation():
    returns = pd.DataFrame(
        {
            "A": [0.01, 0.02, -0.01, 0.03],
            "B": [0.02, 0.03, -0.02, 0.04],
            "C": [-0.01, -0.02, 0.01, -0.03],
        }
    )

    value = average_pairwise_correlation(returns)

    assert -1 <= value <= 1
