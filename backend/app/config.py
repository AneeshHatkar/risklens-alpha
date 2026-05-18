from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RiskLens Alpha"
    app_env: str = "development"
    app_version: str = "0.1.0"
    debug: bool = True

    market_data_provider: str = "yfinance"
    market_data_start_date: str = "2024-01-01"
    market_data_benchmark: str = "SPY"
    market_data_timeout_seconds: int = 20

    alpha_vantage_api_key: str | None = None
    polygon_api_key: str | None = None
    finnhub_api_key: str | None = None
    news_api_key: str | None = None
    fred_api_key: str | None = None
    openai_api_key: str | None = None

    enable_cache: bool = True
    cache_dir: str = ".cache/risklens"
    cache_ttl_seconds: int = 900

    database_url: str = "sqlite:///./risklens_alpha.db"

    enable_background_jobs: bool = False
    market_refresh_interval_minutes: int = 5
    news_refresh_interval_minutes: int = 30

    enable_no_advice_safety: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def cache_path(self) -> Path:
        return Path(self.cache_dir)

    def configured_optional_providers(self) -> list[str]:
        providers = []

        if self.alpha_vantage_api_key:
            providers.append("alpha_vantage")
        if self.polygon_api_key:
            providers.append("polygon")
        if self.finnhub_api_key:
            providers.append("finnhub")
        if self.news_api_key:
            providers.append("newsapi")
        if self.fred_api_key:
            providers.append("fred")
        if self.openai_api_key:
            providers.append("openai")

        return providers

    def public_config(self) -> dict:
        return {
            "app_name": self.app_name,
            "app_env": self.app_env,
            "app_version": self.app_version,
            "debug": self.debug,
            "market_data_provider": self.market_data_provider,
            "market_data_start_date": self.market_data_start_date,
            "market_data_benchmark": self.market_data_benchmark,
            "enable_cache": self.enable_cache,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "database_url_type": self.database_url.split(":", 1)[0],
            "enable_background_jobs": self.enable_background_jobs,
            "market_refresh_interval_minutes": self.market_refresh_interval_minutes,
            "news_refresh_interval_minutes": self.news_refresh_interval_minutes,
            "enable_no_advice_safety": self.enable_no_advice_safety,
            "configured_optional_providers": self.configured_optional_providers(),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
