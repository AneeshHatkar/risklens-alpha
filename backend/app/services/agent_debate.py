from backend.app.schemas import AgentOpinion, FactorExposure, Portfolio, ShockScenario


def _top_affected_holdings(
    portfolio: Portfolio,
    exposures: list[FactorExposure],
    scenario: ShockScenario,
    limit: int = 3,
) -> list[str]:
    affected = set(scenario.affected_factors)
    scores = {}

    for holding in portfolio.holdings:
        relevant = [
            exposure for exposure in exposures
            if exposure.ticker == holding.ticker and exposure.factor in affected
        ]
        scores[holding.ticker] = sum(e.score * holding.weight for e in relevant)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [ticker for ticker, score in ranked[:limit] if score > 0]


def run_agent_debate(
    portfolio: Portfolio,
    scenario: ShockScenario,
    exposures: list[FactorExposure],
) -> list[AgentOpinion]:
    top_holdings = _top_affected_holdings(portfolio, exposures, scenario)

    affected_factor_text = ", ".join(scenario.affected_factors)

    sector_agent = AgentOpinion(
        agent_name="Sector Agent",
        thesis=(
            f"The selected shock primarily affects sectors and themes connected to "
            f"{affected_factor_text}. Holdings with direct mapped exposure to these factors "
            f"should receive higher vulnerability scores."
        ),
        affected_holdings=top_holdings,
        confidence=0.84,
        evidence=[
            f"Scenario affected factors: {affected_factor_text}.",
            "Holding-level factor mappings were used to identify direct and indirect exposure.",
        ],
        risks=[
            "sector-wide multiple compression",
            "theme crowding",
            "simultaneous pressure across correlated holdings",
        ],
        uncertainty="Sector mappings are based on the current seed exposure map and will improve with richer market data.",
    )

    company_agent = AgentOpinion(
        agent_name="Company Agent",
        thesis=(
            "The most vulnerable holdings are the ones whose business model or investor narrative "
            "is most directly linked to the selected shock factors."
        ),
        affected_holdings=top_holdings,
        confidence=0.80,
        evidence=[
            "Each holding was compared against scenario-relevant factor exposures.",
            "Higher portfolio weights increase the impact of a holding-specific vulnerability.",
        ],
        risks=[
            "earnings expectation reset",
            "growth narrative weakness",
            "holding-level concentration",
        ],
        uncertainty="Company-level reasoning is rule-based in the MVP and should later be enriched with filings and live news.",
    )

    technical_agent = AgentOpinion(
        agent_name="Technical Risk Agent",
        thesis=(
            "The portfolio's vulnerability increases when large holdings share common risk factors, "
            "creating hidden correlation and concentration during market stress."
        ),
        affected_holdings=top_holdings,
        confidence=0.76,
        evidence=[
            "The MVP uses shared factor exposure as a proxy for correlation risk.",
            "Concentration and volatility proxies are included in the final score.",
        ],
        risks=[
            "correlation spike",
            "volatility expansion",
            "diversification breakdown",
        ],
        uncertainty="Live return correlations and drawdown metrics will be added in the market data phase.",
    )

    contrarian_agent = AgentOpinion(
        agent_name="Contrarian Agent",
        thesis=(
            "The scenario may be less damaging if demand remains resilient, if affected companies "
            "have diversified revenue streams, or if the market has already priced in part of the risk."
        ),
        affected_holdings=top_holdings[:2],
        confidence=0.62,
        evidence=[
            "A shock scenario is hypothetical and depends on severity, timing, and market expectations.",
            "Some holdings may have offsetting business segments not fully captured by the MVP factor map.",
        ],
        risks=[
            "overstating single-narrative exposure",
            "missing offsetting fundamentals",
            "scenario severity uncertainty",
        ],
        uncertainty="Contrarian analysis should be improved with live fundamentals, earnings transcripts, and valuation data.",
    )

    aggregator = AgentOpinion(
        agent_name="Aggregator/Judge",
        thesis=(
            "The final thesis combines sector exposure, company-level vulnerability, technical concentration, "
            "and contrarian uncertainty into one explainable risk view."
        ),
        affected_holdings=top_holdings,
        confidence=0.81,
        evidence=[
            "Multiple agents identify overlapping exposure in the same holdings.",
            "The final score uses both structured factor mappings and agent consensus.",
        ],
        risks=[
            "overlapping factor exposure",
            "portfolio concentration",
            "scenario-factor alignment",
        ],
        uncertainty="The MVP is educational and does not forecast exact future returns.",
    )

    return [
        sector_agent,
        company_agent,
        technical_agent,
        contrarian_agent,
        aggregator,
    ]
