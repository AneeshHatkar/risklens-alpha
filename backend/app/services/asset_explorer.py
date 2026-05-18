from backend.app.schemas import AssetProfile, FactorExposure, Portfolio
from backend.app.services.asset_metadata import get_asset_metadata, normalize_ticker, search_assets
from backend.app.services.factor_mapper import TICKER_FACTOR_MAP, map_factors
from backend.app.services.market_metrics import compute_market_metrics
from backend.app.services.scenario_generator import SCENARIOS


def find_assets(query: str, limit: int = 10):
    return search_assets(query=query, limit=limit)


def get_factor_exposures_for_ticker(ticker: str) -> list[FactorExposure]:
    clean_ticker = normalize_ticker(ticker)
    factor_map = TICKER_FACTOR_MAP.get(clean_ticker, {})

    exposures = []

    for factor, values in factor_map.items():
        score, confidence, evidence = values

        exposures.append(
            FactorExposure(
                ticker=clean_ticker,
                factor=factor,
                score=score,
                confidence=confidence,
                evidence=evidence,
            )
        )

    return sorted(exposures, key=lambda item: item.score, reverse=True)


def get_related_scenarios_for_ticker(ticker: str) -> list[str]:
    exposures = get_factor_exposures_for_ticker(ticker)
    exposed_factors = {
        exposure.factor
        for exposure in exposures
        if exposure.score >= 0.50
    }

    related = []

    for scenario_id, scenario in SCENARIOS.items():
        if exposed_factors.intersection(set(scenario.affected_factors)):
            related.append(scenario_id)

    return related


def get_latest_price_from_metrics(metrics: dict | None, ticker: str) -> float | None:
    # Current market_metrics service returns risk metrics, not raw latest close yet.
    # This placeholder keeps AssetProfile stable until we add price snapshots/cache.
    return None


def build_single_asset_portfolio(ticker: str) -> Portfolio:
    return Portfolio(
        name=f"{ticker} Single-Asset Research Portfolio",
        holdings=[
            {
                "ticker": ticker,
                "weight": 1.0,
            }
        ],
    )


def get_asset_profile(
    ticker: str,
    use_market_data: bool = True,
) -> AssetProfile:
    clean_ticker = normalize_ticker(ticker)
    metadata = get_asset_metadata(clean_ticker)

    warnings = []

    if metadata is None:
        metadata = {
            "name": clean_ticker,
            "asset_type": "unknown",
            "sector": None,
            "industry": None,
            "description": "No seed metadata is available for this ticker yet.",
        }
        warnings.append("No seed metadata found. Market data may still be attempted.")

    factor_exposures = get_factor_exposures_for_ticker(clean_ticker)

    if not factor_exposures:
        warnings.append("No factor exposure mapping found for this ticker yet.")

    market_metrics = None

    if use_market_data:
        try:
            portfolio = Portfolio(
                name=f"{clean_ticker} Research Portfolio",
                holdings=[
                    {
                        "ticker": clean_ticker,
                        "weight": 1.0,
                    }
                ],
            )
            market_metrics = compute_market_metrics(
                portfolio=portfolio,
                start="2024-01-01",
                benchmark="SPY",
            )
        except Exception as error:
            warnings.append(f"Market data could not be loaded: {error}")

    return AssetProfile(
        ticker=clean_ticker,
        name=metadata["name"],
        asset_type=metadata.get("asset_type", "equity"),
        sector=metadata.get("sector"),
        industry=metadata.get("industry"),
        description=metadata.get("description"),
        latest_price=get_latest_price_from_metrics(market_metrics, clean_ticker),
        currency=None,
        market_metrics=market_metrics,
        factor_exposures=factor_exposures,
        related_scenarios=get_related_scenarios_for_ticker(clean_ticker),
        warnings=warnings,
    )
