from backend.app.config import Settings, get_settings


def test_default_settings_load():
    settings = get_settings()

    assert settings.app_name == "RiskLens Alpha"
    assert settings.market_data_provider == "yfinance"
    assert settings.market_data_benchmark == "SPY"
    assert settings.database_url.startswith("sqlite")


def test_public_config_does_not_expose_api_keys():
    settings = Settings(
        alpha_vantage_api_key="secret-alpha",
        polygon_api_key="secret-polygon",
        openai_api_key="secret-openai",
    )

    public = settings.public_config()
    text = str(public)

    assert "secret-alpha" not in text
    assert "secret-polygon" not in text
    assert "secret-openai" not in text
    assert "alpha_vantage" in public["configured_optional_providers"]
    assert "polygon" in public["configured_optional_providers"]
    assert "openai" in public["configured_optional_providers"]


def test_cache_path_returns_path_object():
    settings = Settings(cache_dir=".cache/test-risklens")

    assert settings.cache_path().name == "test-risklens"
