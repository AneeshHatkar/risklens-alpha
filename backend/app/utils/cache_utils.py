from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pandas as pd

from backend.app.config import get_settings


def safe_cache_key(value: str) -> str:
    clean = value.strip().upper()
    clean = re.sub(r"[^A-Z0-9._-]+", "_", clean)
    return clean.strip("_")


def ensure_cache_dir(subdir: str = "") -> Path:
    settings = get_settings()
    base = settings.cache_path()

    if subdir:
        base = base / subdir

    base.mkdir(parents=True, exist_ok=True)
    return base


def cache_file_is_fresh(path: Path, ttl_seconds: int | None = None) -> bool:
    if not path.exists():
        return False

    settings = get_settings()
    ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds

    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds <= ttl


def write_dataframe_cache(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)


def read_dataframe_cache(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=True)


def write_json_cache(data: dict | list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def read_json_cache(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
