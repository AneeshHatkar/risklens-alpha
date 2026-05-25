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
        "geopolitical risk": (0.62, 0.70, ["AI chip export controls and supply-chain concentration create geopolitical exposure."]),
        "hardware supply chain": (0.72, 0.78, ["GPU supply depends on advanced semiconductor manufacturing and hardware supply chains."]),
    },
    "AMD": {
        "AI infrastructure": (0.82, 0.82, ["AMD has AI accelerator and data center GPU exposure."]),
        "semiconductors": (0.93, 0.90, ["AMD is a major semiconductor company."]),
        "China exposure": (0.58, 0.70, ["Chip export restrictions can affect advanced semiconductor demand channels."]),
        "hardware supply chain": (0.72, 0.80, ["AMD depends on advanced foundry and hardware supply-chain capacity."]),
        "geopolitical risk": (0.60, 0.72, ["Semiconductor supply chains are exposed to geopolitical disruption."]),
        "valuation multiples": (0.76, 0.76, ["High-growth chip names can be sensitive to valuation compression."]),
        "market beta": (0.86, 0.80, ["AMD has elevated semiconductor and growth-stock beta."]),
    },
    "TSM": {
        "semiconductors": (0.96, 0.94, ["TSM is a leading semiconductor foundry."]),
        "hardware supply chain": (0.92, 0.90, ["TSM is central to the advanced semiconductor manufacturing chain."]),
        "China exposure": (0.82, 0.86, ["TSM has direct Taiwan/China geopolitical exposure."]),
        "geopolitical risk": (0.92, 0.88, ["Taiwan geopolitical risk is central to TSM's risk profile."]),
        "AI infrastructure": (0.70, 0.78, ["AI chips depend heavily on advanced foundry manufacturing."]),
        "market beta": (0.72, 0.72, ["TSM has global semiconductor cycle exposure."]),
    },
    "ASML": {
        "semiconductors": (0.92, 0.90, ["ASML is critical to advanced semiconductor equipment."]),
        "hardware supply chain": (0.88, 0.86, ["ASML is a key supplier in advanced lithography supply chains."]),
        "China exposure": (0.72, 0.78, ["ASML can be affected by export restrictions involving advanced chipmaking tools."]),
        "geopolitical risk": (0.75, 0.78, ["Semiconductor equipment exports are exposed to geopolitical restrictions."]),
        "AI infrastructure": (0.62, 0.72, ["Advanced AI chips depend on leading-edge manufacturing equipment."]),
        "valuation multiples": (0.66, 0.72, ["Semiconductor equipment valuations can reset with cycle expectations."]),
    },
    "SMH": {
        "AI infrastructure": (0.80, 0.85, ["SMH includes semiconductor companies exposed to AI infrastructure."]),
        "semiconductors": (0.97, 0.95, ["SMH is a semiconductor ETF."]),
        "China exposure": (0.65, 0.72, ["Semiconductor supply chains and demand can be exposed to China-related restrictions."]),
        "hardware supply chain": (0.76, 0.80, ["SMH components are tied to semiconductor hardware supply chains."]),
        "geopolitical risk": (0.68, 0.75, ["Semiconductor ETFs are exposed to global chip-policy and supply-chain risks."]),
        "valuation multiples": (0.78, 0.80, ["Semiconductor valuations can be sensitive to growth expectation resets."]),
        "market beta": (0.82, 0.80, ["Semiconductor ETFs can show elevated market sensitivity."]),
    },
    "QCOM": {
        "semiconductors": (0.82, 0.82, ["QCOM is a major semiconductor and wireless technology company."]),
        "consumer demand": (0.62, 0.72, ["Smartphone and device demand affect QCOM's business."]),
        "hardware cycle": (0.70, 0.76, ["QCOM is tied to mobile and device hardware cycles."]),
        "China exposure": (0.62, 0.70, ["QCOM has material China-linked demand and supply-chain exposure."]),
        "market beta": (0.68, 0.70, ["QCOM has cyclical semiconductor exposure."]),
    },
    "AVGO": {
        "semiconductors": (0.86, 0.84, ["AVGO has broad semiconductor and infrastructure software exposure."]),
        "AI infrastructure": (0.65, 0.76, ["AVGO participates in AI networking and custom silicon infrastructure."]),
        "hardware supply chain": (0.62, 0.72, ["AVGO is exposed to semiconductor supply-chain cycles."]),
        "valuation multiples": (0.62, 0.70, ["AVGO can be affected by growth and semiconductor valuation resets."]),
        "market beta": (0.70, 0.72, ["AVGO has broad technology-market sensitivity."]),
    },

    "MSFT": {
        "AI infrastructure": (0.70, 0.82, ["MSFT is exposed to AI infrastructure through Azure and AI platform investment."]),
        "cloud growth": (0.92, 0.92, ["Azure growth is a major driver of MSFT's cloud narrative."]),
        "AI software monetization": (0.86, 0.86, ["MSFT is tied to AI monetization through Copilot and enterprise AI products."]),
        "enterprise IT spend": (0.80, 0.84, ["MSFT revenue is connected to enterprise software and cloud spending."]),
        "big-tech correlation": (0.78, 0.85, ["MSFT is a mega-cap technology holding often correlated with broad tech indices."]),
        "valuation multiples": (0.68, 0.78, ["Large-cap growth valuations can be affected by rate and growth expectations."]),
        "market beta": (0.62, 0.75, ["MSFT contributes broad market and technology beta exposure."]),
        "big-tech regulation": (0.58, 0.66, ["MSFT can be exposed to regulatory scrutiny of large technology platforms."]),
    },
    "AAPL": {
        "consumer demand": (0.82, 0.88, ["AAPL hardware sales are sensitive to consumer upgrade cycles and demand."]),
        "hardware cycle": (0.86, 0.88, ["iPhone and device cycles are central to AAPL's business exposure."]),
        "big-tech correlation": (0.72, 0.82, ["AAPL is a major mega-cap technology holding."]),
        "valuation multiples": (0.58, 0.75, ["AAPL can be affected by broad mega-cap valuation resets."]),
        "market beta": (0.58, 0.75, ["AAPL contributes broad equity market exposure."]),
        "China exposure": (0.55, 0.70, ["AAPL has supply-chain and demand exposure connected to China."]),
        "big-tech regulation": (0.54, 0.65, ["AAPL can be exposed to app-store and platform regulation."]),
        "international revenue": (0.70, 0.76, ["AAPL generates substantial revenue outside the United States."]),
    },
    "GOOGL": {
        "AI software monetization": (0.72, 0.78, ["GOOGL is exposed to AI monetization through search, ads, cloud, and AI products."]),
        "cloud growth": (0.72, 0.78, ["Google Cloud growth contributes to GOOGL's cloud narrative."]),
        "advertising revenue": (0.90, 0.90, ["GOOGL is highly exposed to digital advertising revenue."]),
        "big-tech correlation": (0.76, 0.82, ["GOOGL is a mega-cap technology holding."]),
        "valuation multiples": (0.66, 0.76, ["GOOGL's valuation can reset with growth expectations and rates."]),
        "platform risk": (0.82, 0.84, ["Search, ads, and platform regulation are key GOOGL risk themes."]),
        "big-tech regulation": (0.86, 0.86, ["GOOGL is exposed to antitrust and platform regulation."]),
        "market beta": (0.66, 0.72, ["GOOGL contributes broad technology-market exposure."]),
    },
    "AMZN": {
        "cloud growth": (0.78, 0.82, ["AWS growth is a major driver of AMZN's cloud narrative."]),
        "consumer demand": (0.72, 0.78, ["AMZN retail is sensitive to consumer demand."]),
        "enterprise IT spend": (0.66, 0.74, ["AWS spending connects AMZN to enterprise IT cycles."]),
        "valuation multiples": (0.70, 0.76, ["AMZN valuation can be sensitive to growth expectations and rates."]),
        "big-tech correlation": (0.70, 0.78, ["AMZN often trades with mega-cap technology risk sentiment."]),
        "AI infrastructure": (0.58, 0.70, ["AMZN is exposed to AI infrastructure through AWS."]),
        "market beta": (0.70, 0.76, ["AMZN has growth-stock beta exposure."]),
    },
    "META": {
        "advertising revenue": (0.90, 0.90, ["META is highly exposed to digital advertising revenue."]),
        "big-tech correlation": (0.78, 0.82, ["META is a mega-cap technology holding."]),
        "valuation multiples": (0.72, 0.78, ["META valuation can reset with growth expectations."]),
        "AI software monetization": (0.62, 0.70, ["META is investing heavily in AI products and infrastructure."]),
        "big-tech regulation": (0.84, 0.84, ["META is exposed to privacy, antitrust, and platform regulation."]),
        "platform risk": (0.86, 0.84, ["META is exposed to platform, social media, and advertising ecosystem risks."]),
        "market beta": (0.76, 0.78, ["META has elevated technology and growth-stock beta."]),
    },
    "CRM": {
        "cloud growth": (0.68, 0.76, ["CRM is tied to cloud software spending."]),
        "enterprise IT spend": (0.86, 0.86, ["CRM revenue depends on enterprise software budgets."]),
        "AI software monetization": (0.58, 0.68, ["CRM is exposed to AI monetization through enterprise software products."]),
        "valuation multiples": (0.72, 0.76, ["SaaS valuations can be sensitive to growth and rate expectations."]),
        "market beta": (0.70, 0.72, ["CRM has software-growth market sensitivity."]),
    },
    "NOW": {
        "cloud growth": (0.72, 0.78, ["NOW is tied to enterprise workflow and cloud software growth."]),
        "enterprise IT spend": (0.88, 0.86, ["NOW depends heavily on enterprise IT spending."]),
        "AI software monetization": (0.62, 0.70, ["NOW is exposed to AI-enabled enterprise automation."]),
        "valuation multiples": (0.76, 0.78, ["High-growth software valuations can reset under rate pressure."]),
        "market beta": (0.72, 0.72, ["NOW has software-growth market sensitivity."]),
    },
    "ADBE": {
        "AI software monetization": (0.62, 0.70, ["ADBE is exposed to AI monetization in creative and document software."]),
        "enterprise IT spend": (0.62, 0.70, ["ADBE depends partly on enterprise software budgets."]),
        "valuation multiples": (0.70, 0.76, ["ADBE valuation is sensitive to software growth expectations."]),
        "market beta": (0.62, 0.70, ["ADBE has broad software and technology beta."]),
    },

    "SPY": {
        "market beta": (0.95, 0.95, ["SPY represents broad U.S. equity market exposure."]),
        "big-tech correlation": (0.70, 0.78, ["SPY has meaningful mega-cap technology weight."]),
        "valuation multiples": (0.58, 0.72, ["Broad equity indices can be affected by valuation compression."]),
        "consumer demand": (0.45, 0.65, ["Broad equity exposure includes consumer-sensitive sectors."]),
        "interest rates": (0.50, 0.70, ["Broad equities can be sensitive to rate expectations."]),
        "earnings growth": (0.68, 0.74, ["SPY is exposed to broad U.S. earnings growth."]),
    },
    "QQQ": {
        "AI infrastructure": (0.62, 0.76, ["QQQ has significant mega-cap technology and AI-related exposure."]),
        "cloud growth": (0.68, 0.78, ["QQQ includes major cloud and software platform companies."]),
        "big-tech correlation": (0.94, 0.92, ["QQQ is heavily concentrated in mega-cap technology."]),
        "valuation multiples": (0.82, 0.85, ["Growth-heavy indices are sensitive to valuation compression."]),
        "market beta": (0.78, 0.82, ["QQQ has elevated growth and technology beta."]),
        "growth stocks": (0.90, 0.88, ["QQQ is a growth-heavy ETF."]),
        "interest rates": (0.72, 0.78, ["Growth-heavy ETFs are sensitive to interest-rate expectations."]),
    },
    "ARKK": {
        "growth stocks": (0.95, 0.90, ["ARKK is highly exposed to speculative growth stocks."]),
        "valuation multiples": (0.92, 0.86, ["ARKK holdings can be highly sensitive to valuation compression."]),
        "interest rates": (0.82, 0.82, ["Long-duration growth portfolios are sensitive to higher rates."]),
        "market beta": (0.90, 0.84, ["ARKK can show high risk-on/risk-off sensitivity."]),
        "long-duration assets": (0.88, 0.82, ["ARKK resembles a long-duration equity growth basket."]),
    },

    "TLT": {
        "interest rates": (0.96, 0.94, ["TLT is highly sensitive to long-term interest-rate moves."]),
        "long-duration assets": (0.98, 0.94, ["TLT is a long-duration Treasury ETF."]),
        "liquidity conditions": (0.58, 0.66, ["Long bonds can react to liquidity and risk-off dynamics."]),
        "market beta": (0.25, 0.50, ["TLT can behave differently from equities but affects portfolio risk."]),
    },
    "GLD": {
        "inflation": (0.58, 0.66, ["Gold can react to inflation expectations and real-rate dynamics."]),
        "geopolitical risk": (0.70, 0.72, ["Gold can behave as a safe-haven asset in geopolitical stress."]),
        "dollar strength": (0.62, 0.68, ["Gold can be pressured by U.S. dollar strength."]),
        "market beta": (0.18, 0.45, ["Gold usually has lower direct equity beta."]),
    },
    "DBC": {
        "commodity pressure": (0.92, 0.88, ["DBC is a broad commodities ETF."]),
        "oil prices": (0.76, 0.80, ["Energy commodities are a meaningful part of commodity baskets."]),
        "inflation": (0.78, 0.78, ["Commodities can be linked to inflation shocks."]),
        "dollar strength": (0.65, 0.70, ["Commodities can be sensitive to U.S. dollar strength."]),
    },
    "XLE": {
        "oil prices": (0.95, 0.92, ["XLE is an energy-sector ETF highly exposed to oil and gas prices."]),
        "inflation": (0.66, 0.72, ["Energy can be linked to inflation shocks."]),
        "commodity pressure": (0.82, 0.82, ["XLE is exposed to energy commodity cycles."]),
        "market beta": (0.62, 0.70, ["Energy equities still carry broad market risk."]),
    },
    "CVX": {
        "oil prices": (0.88, 0.88, ["CVX is directly exposed to oil and gas price cycles."]),
        "inflation": (0.58, 0.66, ["Energy producers can benefit from some inflationary commodity shocks."]),
        "commodity pressure": (0.78, 0.78, ["CVX has commodity-cycle exposure."]),
        "market beta": (0.55, 0.66, ["CVX has broad equity-market exposure."]),
    },
    "XOM": {
        "oil prices": (0.90, 0.90, ["XOM is directly exposed to oil and gas price cycles."]),
        "inflation": (0.58, 0.66, ["Energy producers can be linked to inflationary commodity shocks."]),
        "commodity pressure": (0.80, 0.80, ["XOM has commodity-cycle exposure."]),
        "market beta": (0.55, 0.66, ["XOM has broad equity-market exposure."]),
    },

    "JPM": {
        "banking stress": (0.76, 0.82, ["JPM is a major bank exposed to financial-sector stress."]),
        "credit risk": (0.72, 0.78, ["Bank earnings and balance sheets are exposed to credit-cycle risk."]),
        "interest rates": (0.66, 0.74, ["Bank profitability and securities portfolios are affected by rate dynamics."]),
        "deposit flight": (0.45, 0.62, ["Large banks can be affected by deposit competition and funding costs."]),
        "market beta": (0.62, 0.70, ["JPM has broad financial-sector market exposure."]),
    },
    "BAC": {
        "banking stress": (0.82, 0.84, ["BAC is exposed to broad banking-sector stress."]),
        "credit risk": (0.76, 0.80, ["BAC is exposed to credit-cycle losses and lending conditions."]),
        "interest rates": (0.72, 0.78, ["BAC earnings and securities portfolio can be sensitive to rates."]),
        "deposit flight": (0.58, 0.70, ["BAC can be affected by deposit competition and funding pressure."]),
        "market beta": (0.70, 0.72, ["BAC has financial-sector beta."]),
    },
    "WFC": {
        "banking stress": (0.82, 0.84, ["WFC is exposed to broad banking-sector stress."]),
        "credit risk": (0.76, 0.80, ["WFC is exposed to lending and credit-cycle risk."]),
        "interest rates": (0.68, 0.76, ["WFC earnings can be affected by rate and funding conditions."]),
        "deposit flight": (0.58, 0.70, ["WFC can be affected by deposit competition and funding pressure."]),
        "market beta": (0.70, 0.72, ["WFC has financial-sector beta."]),
    },
    "KRE": {
        "banking stress": (0.96, 0.92, ["KRE is a regional bank ETF directly exposed to regional banking stress."]),
        "credit risk": (0.84, 0.86, ["Regional banks are exposed to credit tightening and loan losses."]),
        "deposit flight": (0.92, 0.90, ["Regional banks are sensitive to deposit outflows and funding pressure."]),
        "interest rates": (0.72, 0.78, ["Regional banks are sensitive to rate and securities-portfolio dynamics."]),
        "market beta": (0.76, 0.78, ["KRE has financial-sector market sensitivity."]),
    },
    "SCHW": {
        "banking stress": (0.72, 0.78, ["SCHW can be affected by financial-sector funding and deposit dynamics."]),
        "deposit flight": (0.76, 0.80, ["SCHW has exposure to client cash and deposit movement."]),
        "interest rates": (0.72, 0.78, ["SCHW can be affected by rate and cash-sweep economics."]),
        "market beta": (0.70, 0.72, ["SCHW has financial-sector and brokerage market sensitivity."]),
    },

    "TSLA": {
        "consumer demand": (0.82, 0.82, ["TSLA vehicle demand is sensitive to consumer spending and financing conditions."]),
        "discretionary spending": (0.88, 0.84, ["Auto purchases are discretionary and financing-sensitive."]),
        "interest rates": (0.68, 0.74, ["Higher rates can pressure auto affordability and growth valuations."]),
        "valuation multiples": (0.86, 0.82, ["TSLA valuation is sensitive to growth expectations."]),
        "market beta": (0.92, 0.86, ["TSLA has high market and growth-stock beta."]),
    },
    "HD": {
        "consumer demand": (0.76, 0.80, ["HD is sensitive to housing and consumer home-improvement demand."]),
        "discretionary spending": (0.72, 0.78, ["Home improvement spending is partly discretionary."]),
        "interest rates": (0.68, 0.74, ["Higher rates can pressure housing activity and home improvement demand."]),
        "earnings growth": (0.60, 0.70, ["HD earnings depend on consumer and housing cycles."]),
        "market beta": (0.55, 0.65, ["HD carries broad consumer cyclicality."]),
    },
    "NKE": {
        "consumer demand": (0.78, 0.80, ["NKE is sensitive to consumer spending and global apparel demand."]),
        "discretionary spending": (0.84, 0.82, ["Athletic apparel and footwear include discretionary spending exposure."]),
        "China exposure": (0.55, 0.68, ["NKE has international and China-linked revenue exposure."]),
        "international revenue": (0.70, 0.76, ["NKE generates substantial revenue globally."]),
        "market beta": (0.58, 0.66, ["NKE carries consumer discretionary market exposure."]),
    },
    "SBUX": {
        "consumer demand": (0.78, 0.80, ["SBUX is sensitive to consumer traffic and discretionary food/beverage spending."]),
        "discretionary spending": (0.72, 0.76, ["Premium coffee spending can weaken in consumer slowdowns."]),
        "China exposure": (0.58, 0.68, ["SBUX has meaningful China growth exposure."]),
        "international revenue": (0.62, 0.70, ["SBUX has global revenue exposure."]),
        "market beta": (0.56, 0.66, ["SBUX has consumer discretionary market exposure."]),
    },
    "WMT": {
        "consumer demand": (0.50, 0.68, ["WMT is exposed to consumer spending but can be defensive in downturns."]),
        "discretionary spending": (0.30, 0.55, ["WMT has less discretionary exposure than many retailers."]),
        "earnings growth": (0.42, 0.60, ["WMT earnings are linked to retail demand and margins."]),
        "market beta": (0.35, 0.55, ["WMT tends to be more defensive than high-beta equities."]),
    },
    "COST": {
        "consumer demand": (0.50, 0.68, ["COST is exposed to consumer spending but can be defensive."]),
        "discretionary spending": (0.35, 0.58, ["COST has lower discretionary exposure than many retailers."]),
        "valuation multiples": (0.58, 0.66, ["COST's premium valuation can be sensitive to multiple compression."]),
        "market beta": (0.42, 0.58, ["COST tends to be defensive but still has equity risk."]),
    },
    "PG": {
        "consumer demand": (0.34, 0.55, ["PG sells consumer staples with relatively defensive demand."]),
        "earnings growth": (0.35, 0.55, ["PG earnings are more defensive but still affected by margins and demand."]),
        "market beta": (0.28, 0.50, ["PG is usually lower beta than broad equities."]),
        "inflation": (0.42, 0.58, ["PG can be affected by input-cost inflation and pricing power."]),
    },

    "XLU": {
        "interest rates": (0.66, 0.72, ["Utilities can be sensitive to interest rates due to dividend and debt dynamics."]),
        "market beta": (0.35, 0.55, ["XLU is generally defensive but not risk-free."]),
        "earnings growth": (0.30, 0.50, ["Utilities tend to have more stable earnings profiles."]),
    },
    "XLV": {
        "market beta": (0.42, 0.58, ["Healthcare ETFs tend to be defensive but still carry market exposure."]),
        "earnings growth": (0.45, 0.60, ["Healthcare earnings can be more defensive but still matter."]),
        "consumer demand": (0.25, 0.45, ["Healthcare demand is less discretionary than retail demand."]),
    },
    "VEA": {
        "international revenue": (0.82, 0.82, ["VEA represents developed international equity exposure."]),
        "dollar strength": (0.72, 0.78, ["International assets can be affected by U.S. dollar strength."]),
        "market beta": (0.70, 0.74, ["VEA has global equity beta."]),
        "earnings growth": (0.58, 0.66, ["VEA is exposed to developed-market earnings cycles."]),
    },
    "EEM": {
        "emerging markets": (0.94, 0.90, ["EEM represents emerging-market equity exposure."]),
        "dollar strength": (0.82, 0.84, ["Emerging markets can be pressured by a strong U.S. dollar."]),
        "China exposure": (0.72, 0.78, ["EEM has meaningful China and Asia exposure."]),
        "market beta": (0.78, 0.78, ["Emerging markets can have elevated global risk beta."]),
    },
    "BABA": {
        "China exposure": (0.92, 0.90, ["BABA has direct China business and regulatory exposure."]),
        "emerging markets": (0.70, 0.76, ["BABA is a major emerging-market technology exposure."]),
        "platform risk": (0.74, 0.78, ["BABA is exposed to platform and regulatory risk."]),
        "consumer demand": (0.62, 0.70, ["BABA's commerce business is tied to Chinese consumer demand."]),
        "market beta": (0.76, 0.78, ["BABA can show elevated emerging-market technology beta."]),
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
