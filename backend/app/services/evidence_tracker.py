from backend.app.schemas import (
    AgentOpinion,
    EvidenceItem,
    FactorExposure,
    HoldingRisk,
    Portfolio,
    ShockScenario,
)


def build_factor_mapping_evidence(
    exposures: list[FactorExposure],
    scenario: ShockScenario,
) -> list[EvidenceItem]:
    affected = set(scenario.affected_factors)
    items = []

    for exposure in exposures:
        if exposure.factor not in affected:
            continue

        items.append(
            EvidenceItem(
                evidence_type="factor_mapping",
                claim=f"{exposure.ticker} is exposed to {exposure.factor}.",
                source="seed_factor_map",
                ticker=exposure.ticker,
                factor=exposure.factor,
                value=round(exposure.score, 4),
                confidence=round(exposure.confidence, 4),
                details={
                    "scenario": scenario.name,
                    "scenario_severity": scenario.severity,
                    "raw_evidence": exposure.evidence,
                },
            )
        )

    return items


def build_market_metric_evidence(
    market_metrics: dict | None,
) -> list[EvidenceItem]:
    if not market_metrics:
        return []

    items = []
    asset_metrics = market_metrics.get("asset_metrics", {})
    portfolio_metrics = market_metrics.get("portfolio_metrics", {})

    if "portfolio_volatility" in portfolio_metrics:
        items.append(
            EvidenceItem(
                evidence_type="market_metric",
                claim="Portfolio volatility was included in the vulnerability analysis.",
                source="market_data_cache_or_yfinance",
                value=portfolio_metrics["portfolio_volatility"],
                confidence=0.90,
                details={
                    "metric": "portfolio_volatility",
                    "benchmark": portfolio_metrics.get("benchmark"),
                    "used_cache": portfolio_metrics.get("used_cache"),
                    "warnings": portfolio_metrics.get("warnings", []),
                },
            )
        )

    if "average_pairwise_correlation" in portfolio_metrics:
        items.append(
            EvidenceItem(
                evidence_type="market_metric",
                claim="Average pairwise correlation was included in the vulnerability analysis.",
                source="market_data_cache_or_yfinance",
                value=portfolio_metrics["average_pairwise_correlation"],
                confidence=0.90,
                details={
                    "metric": "average_pairwise_correlation",
                    "benchmark": portfolio_metrics.get("benchmark"),
                    "used_cache": portfolio_metrics.get("used_cache"),
                },
            )
        )

    for ticker, metrics in asset_metrics.items():
        if not metrics.get("available"):
            continue

        for metric in ["volatility", "beta", "max_drawdown", "cumulative_return"]:
            if metric not in metrics:
                continue

            items.append(
                EvidenceItem(
                    evidence_type="market_metric",
                    claim=f"{ticker} {metric.replace('_', ' ')} was included in holding-level risk analysis.",
                    source="market_data_cache_or_yfinance",
                    ticker=ticker,
                    factor=metric,
                    value=metrics[metric],
                    confidence=0.90,
                    details={
                        "metric": metric,
                    },
                )
            )

    return items


def build_agent_evidence(
    agent_opinions: list[AgentOpinion],
) -> list[EvidenceItem]:
    items = []

    for agent in agent_opinions:
        items.append(
            EvidenceItem(
                evidence_type="agent_opinion",
                claim=agent.thesis,
                source=agent.agent_name,
                confidence=round(agent.confidence, 4),
                details={
                    "affected_holdings": agent.affected_holdings,
                    "risks": agent.risks,
                    "evidence": agent.evidence,
                    "uncertainty": agent.uncertainty,
                },
            )
        )

    return items


def build_holding_risk_evidence(
    holding_risks: list[HoldingRisk],
) -> list[EvidenceItem]:
    items = []

    for holding in holding_risks:
        items.append(
            EvidenceItem(
                evidence_type="holding_risk",
                claim=f"{holding.ticker} received a holding risk score of {holding.risk_score}/100.",
                source="risk_scoring_engine",
                ticker=holding.ticker,
                value=holding.risk_score,
                confidence=None,
                details={
                    "risk_level": holding.risk_level,
                    "reasons": holding.reasons,
                },
            )
        )

    return items


def build_hidden_concentration_evidence(
    hidden_concentration: dict | None,
) -> list[EvidenceItem]:
    if not hidden_concentration:
        return []

    return [
        EvidenceItem(
            evidence_type="hidden_concentration",
            claim=hidden_concentration["explanation"],
            source="hidden_concentration_engine",
            value=hidden_concentration["score"],
            confidence=None,
            details={
                "level": hidden_concentration["level"],
                "direct_hhi": hidden_concentration["direct_hhi"],
                "dominant_themes": hidden_concentration["dominant_themes"],
            },
        )
    ]


def build_simulation_evidence(
    portfolio: Portfolio,
    scenario: ShockScenario,
    exposures: list[FactorExposure],
    holding_risks: list[HoldingRisk],
    agent_opinions: list[AgentOpinion],
    hidden_concentration: dict | None = None,
    market_metrics: dict | None = None,
) -> list[EvidenceItem]:
    items = []

    items.append(
        EvidenceItem(
            evidence_type="scenario_rule",
            claim=f"The selected shock scenario affects {', '.join(scenario.affected_factors)}.",
            source="scenario_catalog",
            value=scenario.severity,
            confidence=0.90,
            details={
                "scenario_name": scenario.name,
                "description": scenario.description,
                "affected_factors": scenario.affected_factors,
                "portfolio_name": portfolio.name,
            },
        )
    )

    items.extend(build_factor_mapping_evidence(exposures, scenario))
    items.extend(build_market_metric_evidence(market_metrics))
    items.extend(build_holding_risk_evidence(holding_risks))
    items.extend(build_hidden_concentration_evidence(hidden_concentration))
    items.extend(build_agent_evidence(agent_opinions))

    return items
