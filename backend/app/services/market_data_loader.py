from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

import pandas as pd
import yfinance as yf

from backend.app.config import get_settings
from backend.app.utils.cache_utils import (
    cache_file_is_fresh,
    ensure_cache_dir,
    read_dataframe_cache,
    safe_cache_key,
    write_dataframe_cache,
)


@dataclass
class MarketDataResult:
    tickers: list[str]
    start: str
    end: str | None
    prices: pd.DataFrame
    returns: pd.DataFrame
    missing_tickers: list[str]
    warnings: list[str]
    used_cache: bool = False
    cache_path: str | None = None


def normalize_tickers(tickers: Iterable[str]) -> list[str]:
    clean = []

    for ticker in tickers:
        value = ticker.strip().upper()
        if value and value not in clean:
            clean.append(value)

    return clean


def build_price_cache_path(
    tickers: list[str],
    start: str,
    end: str | None,
) -> str:
    joined = "_".join(sorted(tickers))
    end_value = end or "latest"
    key = safe_cache_key(f"{joined}_{start}_{end_value}")
    cache_dir = ensure_cache_dir("prices")
    return str(cache_dir / f"{key}.csv")


def load_price_history(
    tickers: Iterable[str],
    start: str = "2023-01-01",
    end: str | None = None,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> MarketDataResult:
    clean_tickers = normalize_tickers(tickers)
    warnings: list[str] = []

    if not clean_tickers:
        raise ValueError("At least one ticker is required to load market data.")

    settings = get_settings()
    cache_path = build_price_cache_path(clean_tickers, start, end)
    from pathlib import Path
    cache_path_obj = Path(cache_path)

    if use_cache and not force_refresh:
        cached = _try_load_cached_prices(cache_path_obj, start, end, clean_tickers)
        if cached is not None:
            prices, missing = cached
            returns = prices.pct_change(fill_method=None).dropna(how="all")
            return MarketDataResult(
                tickers=clean_tickers,
                start=start,
                end=end,
                prices=prices,
                returns=returns,
                missing_tickers=missing,
                warnings=["Loaded market prices from cache."],
                used_cache=True,
                cache_path=cache_path,
            )

    try:
        raw = yf.download(
            tickers=clean_tickers,
            start=start,
            end=end,
            progress=False,
            auto_adjust=True,
            group_by="column",
            threads=True,
            timeout=settings.market_data_timeout_seconds,
        )

        if raw.empty:
            raise ValueError("No market data returned from provider.")

        prices = _extract_close_prices(raw, clean_tickers)
        prices = prices.dropna(how="all")

        missing = [
            ticker for ticker in clean_tickers
            if ticker not in prices.columns or prices[ticker].dropna().empty
        ]

        prices = prices.drop(columns=missing, errors="ignore")

        if prices.empty:
            raise ValueError("No usable close price data found for the requested tickers.")

        if missing:
            warnings.append(f"Missing usable price data for: {', '.join(missing)}")

        if use_cache:
            write_dataframe_cache(prices, Path(cache_path))

        returns = prices.pct_change(fill_method=None).dropna(how="all")

        return MarketDataResult(
            tickers=clean_tickers,
            start=start,
            end=end,
            prices=prices,
            returns=returns,
            missing_tickers=missing,
            warnings=warnings,
            used_cache=False,
            cache_path=cache_path,
        )

    except Exception as error:
        cached = _try_load_cached_prices(cache_path_obj, start, end, clean_tickers, allow_stale=True)

        if cached is not None:
            prices, missing = cached
            returns = prices.pct_change(fill_method=None).dropna(how="all")

            return MarketDataResult(
                tickers=clean_tickers,
                start=start,
                end=end,
                prices=prices,
                returns=returns,
                missing_tickers=missing,
                warnings=[
                    f"Live market data failed: {error}",
                    "Using stale cached market prices as fallback.",
                ],
                used_cache=True,
                cache_path=cache_path,
            )

        raise ValueError(
            f"Market data could not be loaded and no cache fallback is available: {error}"
        ) from error


def _try_load_cached_prices(
    cache_path: str,
    start: str,
    end: str | None,
    tickers: list[str],
    allow_stale: bool = False,
) -> tuple[pd.DataFrame, list[str]] | None:
    from pathlib import Path

    path = Path(cache_path)

    if not path.exists():
        return None

    if not allow_stale and not cache_file_is_fresh(path):
        return None

    try:
        prices = read_dataframe_cache(path)
        prices.columns = [str(col).upper() for col in prices.columns]
        prices = prices.dropna(how="all")

        missing = [
            ticker for ticker in tickers
            if ticker not in prices.columns or prices[ticker].dropna().empty
        ]

        prices = prices.drop(columns=missing, errors="ignore")

        if prices.empty:
            return None

        return prices, missing
    except Exception:
        return None


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
    use_cache: bool = True,
    force_refresh: bool = False,
) -> MarketDataResult:
    tickers = [holding["ticker"] for holding in portfolio_holdings]

    if benchmark.upper() not in [ticker.upper() for ticker in tickers]:
        tickers.append(benchmark)

    return load_price_history(
        tickers=tickers,
        start=start,
        end=end,
        use_cache=use_cache,
        force_refresh=force_refresh,
    )


def today_iso() -> str:
    return date.today().isoformat()


def get_latest_prices(
    tickers: Iterable[str],
    start: str = "2024-01-01",
    use_cache: bool = True,
    force_refresh: bool = False,
) -> dict:
    market_data = load_price_history(
        tickers=tickers,
        start=start,
        use_cache=use_cache,
        force_refresh=force_refresh,
    )

    prices = market_data.prices
    latest_prices = {}

    for ticker in normalize_tickers(tickers):
        if ticker not in prices.columns or prices[ticker].dropna().empty:
            latest_prices[ticker] = {
                "available": False,
                "latest_price": None,
                "warning": "No usable price data found.",
            }
            continue

        latest_prices[ticker] = {
            "available": True,
            "latest_price": round(float(prices[ticker].dropna().iloc[-1]), 4),
            "warning": None,
        }

    return {
        "prices": latest_prices,
        "market_data": {
            "missing_tickers": market_data.missing_tickers,
            "warnings": market_data.warnings,
            "used_cache": market_data.used_cache,
            "cache_path": market_data.cache_path,
        },
    }
