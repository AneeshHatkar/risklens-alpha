from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

import pandas as pd
import yfinance as yf


@dataclass
class MarketDataResult:
    tickers: list[str]
    start: str
    end: str | None
    prices: pd.DataFrame
    returns: pd.DataFrame
    missing_tickers: list[str]


def normalize_tickers(tickers: Iterable[str]) -> list[str]:
    clean = []

    for ticker in tickers:
        value = ticker.strip().upper()
        if value and value not in clean:
            clean.append(value)

    return clean


def load_price_history(
    tickers: Iterable[str],
    start: str = "2023-01-01",
    end: str | None = None,
) -> MarketDataResult:
    clean_tickers = normalize_tickers(tickers)

    if not clean_tickers:
        raise ValueError("At least one ticker is required to load market data.")

    raw = yf.download(
        tickers=clean_tickers,
        start=start,
        end=end,
        progress=False,
        auto_adjust=True,
        group_by="column",
        threads=True,
    )

    if raw.empty:
        raise ValueError("No market data returned. Check ticker symbols or internet connection.")

    prices = _extract_close_prices(raw, clean_tickers)
    prices = prices.dropna(how="all")

    missing = [
        ticker for ticker in clean_tickers
        if ticker not in prices.columns or prices[ticker].dropna().empty
    ]

    prices = prices.drop(columns=missing, errors="ignore")

    if prices.empty:
        raise ValueError("No usable close price data found for the requested tickers.")

    returns = prices.pct_change(fill_method=None).dropna(how="all")

    return MarketDataResult(
        tickers=clean_tickers,
        start=start,
        end=end,
        prices=prices,
        returns=returns,
        missing_tickers=missing,
    )


def _extract_close_prices(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            close = raw["Close"]
        elif "Adj Close" in raw.columns.get_level_values(0):
            close = raw["Adj Close"]
        else:
            raise ValueError("Downloaded market data does not contain close prices.")

        if isinstance(close, pd.Series):
            close = close.to_frame(name=tickers[0])

        close.columns = [str(col).upper() for col in close.columns]
        return close

    if "Close" in raw.columns:
        return raw["Close"].to_frame(name=tickers[0])

    if "Adj Close" in raw.columns:
        return raw["Adj Close"].to_frame(name=tickers[0])

    raise ValueError("Downloaded market data does not contain close prices.")


def load_portfolio_price_history(
    portfolio_holdings: list[dict],
    start: str = "2023-01-01",
    end: str | None = None,
    benchmark: str = "SPY",
) -> MarketDataResult:
    tickers = [holding["ticker"] for holding in portfolio_holdings]

    if benchmark.upper() not in [ticker.upper() for ticker in tickers]:
        tickers.append(benchmark)

    return load_price_history(tickers=tickers, start=start, end=end)


def today_iso() -> str:
    return date.today().isoformat()
