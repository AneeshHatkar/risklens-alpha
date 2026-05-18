from backend.app.services.asset_explorer import (
    find_assets,
    get_asset_profile,
    get_factor_exposures_for_ticker,
    get_related_scenarios_for_ticker,
)


def test_find_assets_returns_nvda():
    results = find_assets("NVDA")

    tickers = [item.ticker for item in results]

    assert "NVDA" in tickers


def test_get_factor_exposures_for_known_ticker():
    exposures = get_factor_exposures_for_ticker("NVDA")

    factors = [item.factor for item in exposures]

    assert "AI infrastructure" in factors
    assert "semiconductors" in factors


def test_get_related_scenarios_for_ticker():
    scenarios = get_related_scenarios_for_ticker("NVDA")

    assert "ai_capex_slowdown" in scenarios
    assert "semiconductor_export_restriction" in scenarios


def test_get_asset_profile_without_market_data():
    profile = get_asset_profile("NVDA", use_market_data=False)

    assert profile.ticker == "NVDA"
    assert profile.name == "NVIDIA Corporation"
    assert profile.market_metrics is None
    assert len(profile.factor_exposures) > 0


def test_unknown_asset_profile_returns_warning():
    profile = get_asset_profile("UNKNOWNXYZ", use_market_data=False)

    assert profile.ticker == "UNKNOWNXYZ"
    assert profile.asset_type == "unknown"
    assert profile.warnings
