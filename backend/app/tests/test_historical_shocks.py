from backend.app.main import load_sample_portfolio
from backend.app.services.historical_shocks import (
    get_historical_shock,
    list_historical_shocks,
    replay_historical_shock,
)
from backend.app.services.portfolio_parser import normalize_portfolio


def test_list_historical_shocks_contains_known_events():
    shocks = list_historical_shocks()

    assert "covid_crash_2020" in shocks
    assert "rate_shock_2022" in shocks


def test_get_historical_shock_returns_catalog_entry():
    shock = get_historical_shock("covid_crash_2020")

    assert shock["name"] == "COVID Crash 2020"
    assert shock["start"] == "2020-02-19"
    assert shock["benchmark"] == "SPY"


def test_historical_replay_returns_expected_shape():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)

    result = replay_historical_shock(
        portfolio=portfolio,
        shock_id="rate_shock_2022",
        use_cache=True,
    )

    assert result["shock_id"] == "rate_shock_2022"
    assert "portfolio_metrics" in result
    assert "asset_impacts" in result
    assert "worst_contributors" in result
    assert "summary" in result
    assert "disclaimer" in result
