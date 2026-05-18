from pathlib import Path

import pandas as pd

from backend.app.utils.cache_utils import (
    cache_file_is_fresh,
    read_dataframe_cache,
    safe_cache_key,
    write_dataframe_cache,
)


def test_safe_cache_key_removes_bad_characters():
    key = safe_cache_key("NVDA/MSFT SPY:2024")

    assert "/" not in key
    assert ":" not in key
    assert " " not in key
    assert "NVDA" in key


def test_dataframe_cache_roundtrip(tmp_path):
    path = tmp_path / "prices.csv"
    df = pd.DataFrame(
        {
            "NVDA": [100.0, 101.0],
            "MSFT": [200.0, 202.0],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )

    write_dataframe_cache(df, path)
    loaded = read_dataframe_cache(path)

    assert path.exists()
    assert list(loaded.columns) == ["NVDA", "MSFT"]
    assert loaded.shape == (2, 2)


def test_cache_file_is_fresh_for_new_file(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("hello", encoding="utf-8")

    assert cache_file_is_fresh(path, ttl_seconds=60)
