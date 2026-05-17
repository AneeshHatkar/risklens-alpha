from backend.app.schemas import FactorExposure, Portfolio, ShockScenario


TICKER_FACTOR_MAP = {
    "NVDA": {
        "AI infrastructure": (0.97, 0.95, ["NVDA is strongly linked to AI accelerator demand and data center GPU spending."]),
        "semiconductors": (0.96, 0.95, ["NVDA is a leading semiconductor company with direct GPU exposure."]),
        "cloud growth": (0.45, 0.75, ["Cloud providers are major buyers of AI accelerators."]),
        "big-tech correlation": (0.75, 0.80, ["NVDA often trades with mega-cap technology and AI growth sentiment."]),
        "valuation multiples": (0.82, 0.78, ["High-growth semiconductor names can be sensitive to valuation resets."]),
        "China exposure": (0.62, 0.70, ["Advanced chip export restrictions may affect semiconductor demand channels."]),
        "market beta": (0.85, 0.80, ["NVDA has historically shown elevated sensitivity to broad risk-on/risk-off moves."]),
    },
    "MSFT": {
        "AI infrastructure": (0.70, 0.82, ["MSFT is exposed to AI infrastructure through Azure and AI platform investment."]),
        "cloud growth": (0.92, 0.92, ["Azure growth is a major driver of MSFT's cloud narrative."]),
        "AI software monetization": (0.86, 0.86, ["MSFT is tied to AI monetization through Copilot and enterprise AI products."]),
        "enterprise IT spend": (0.80, 0.84, ["MSFT revenue is connected to enterprise software and cloud spending."]),
        "big-tech correlation": (0.78, 0.85, ["MSFT is a mega-cap technology holding often correlated with broad tech indices."]),
        "valuation multiples": (0.68, 0.78, ["Large-cap growth valuations can be affected by rate and growth expectations."]),
        "market beta": (0.62, 0.75, ["MSFT contributes broad market and technology beta exposure."]),
    },
    "AAPL": {
        "consumer demand": (0.82, 0.88, ["AAPL hardware sales are sensitive to consumer upgrade cycles and demand."]),
        "hardware cycle": (0.86, 0.88, ["iPhone and device cycles are central to AAPL's business exposure."]),
        "big-tech correlation": (0.72, 0.82, ["AAPL is a major mega-cap technology holding."]),
        "valuation multiples": (0.58, 0.75, ["AAPL can be affected by broad mega-cap valuation resets."]),
        "market beta": (0.58, 0.75, ["AAPL contributes broad equity market exposure."]),
        "China exposure": (0.55, 0.70, ["AAPL has supply-chain and demand exposure connected to China."]),
    },
    "SPY": {
        "market beta": (0.95, 0.95, ["SPY represents broad U.S. equity market exposure."]),
        "big-tech correlation": (0.70, 0.78, ["SPY has meaningful mega-cap technology weight."]),
        "valuation multiples": (0.58, 0.72, ["Broad equity indices can be affected by valuation compression."]),
        "consumer demand": (0.45, 0.65, ["Broad equity exposure includes consumer-sensitive sectors."]),
        "interest rates": (0.50, 0.70, ["Broad equities can be sensitive to rate expectations."]),
    },
    "QQQ": {
        "AI infrastructure": (0.62, 0.76, ["QQQ has significant mega-cap technology and AI-related exposure."]),
        "cloud growth": (0.68, 0.78, ["QQQ includes major cloud and software platform companies."]),
        "big-tech correlation": (0.94, 0.92, ["QQQ is heavily concentrated in mega-cap technology."]),
        "valuation multiples": (0.82, 0.85, ["Growth-heavy indices are sensitive to valuation compression."]),
        "market beta": (0.78, 0.82, ["QQQ has elevated growth and technology beta."]),
        "growth stocks": (0.90, 0.88, ["QQQ is a growth-heavy ETF."]),
    },
    "SMH": {
        "AI infrastructure": (0.80, 0.85, ["SMH includes semiconductor companies exposed to AI infrastructure."]),
        "semiconductors": (0.97, 0.95, ["SMH is a semiconductor ETF."]),
        "China exposure": (0.65, 0.72, ["Semiconductor supply chains and demand can be exposed to China-related restrictions."]),
        "hardware supply chain": (0.76, 0.80, ["SMH components are tied to semiconductor hardware supply chains."]),
        "valuation multiples": (0.78, 0.80, ["Semiconductor valuations can be sensitive to growth expectation resets."]),
        "market beta": (0.82, 0.80, ["Semiconductor ETFs can show elevated market sensitivity."]),
    },
}


DEFAULT_FACTORS = {
    "market beta": (0.55, 0.45, ["Fallback broad market exposure assigned because detailed metadata is unavailable."]),
    "valuation multiples": (0.40, 0.40, ["Fallback valuation exposure assigned because detailed metadata is unavailable."]),
}


def map_factors(portfolio: Portfolio, scenario: ShockScenario) -> list[FactorExposure]:
    exposures: list[FactorExposure] = []

    for holding in portfolio.holdings:
        factor_map = TICKER_FACTOR_MAP.get(holding.ticker, DEFAULT_FACTORS)

        for factor, values in factor_map.items():
            score, confidence, evidence = values

            # Include all factors for explainability, but scenario-affected factors
            # will matter most inside the risk scoring engine.
            exposures.append(
                FactorExposure(
                    ticker=holding.ticker,
                    factor=factor,
                    score=score,
                    confidence=confidence,
                    evidence=evidence,
                )
            )

    return exposures


def get_scenario_relevant_exposures(
    exposures: list[FactorExposure],
    scenario: ShockScenario,
) -> list[FactorExposure]:
    affected = set(scenario.affected_factors)
    return [exposure for exposure in exposures if exposure.factor in affected]
