from pathlib import Path

import pandas as pd

from backend.app.services.market_data_loader import (
    build_price_cache_path,
    load_price_history,
)
from backend.app.utils.cache_utils import write_dataframe_cache


def test_build_price_cache_path_creates_csv_path():
    path = build_price_cache_path(["NVDA", "MSFT"], "2024-01-01", None)

    assert path.endswith(".csv")
    assert "NVDA" in path or "MSFT" in path


def test_load_price_history_uses_fresh_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("CACHE_TTL_SECONDS", "3600")

    # Clear cached settings so env overrides are picked up.
    from backend.app.config import get_settings
    get_settings.cache_clear()

    cache_path = Path(build_price_cache_path(["NVDA", "MSFT"], "2024-01-01", None))

    prices = pd.DataFrame(
        {
            "NVDA": [100.0, 102.0, 104.0],
            "MSFT": [200.0, 201.0, 202.0],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )
    write_dataframe_cache(prices, cache_path)

    result = load_price_history(
        tickers=["NVDA", "MSFT"],
        start="2024-01-01",
        use_cache=True,
        force_refresh=False,
    )

    assert result.used_cache is True
    assert "Loaded market prices from cache." in result.warnings
    assert list(result.prices.columns) == ["NVDA", "MSFT"]

    get_settings.cache_clear()
