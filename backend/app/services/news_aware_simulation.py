from __future__ import annotations

from backend.app.ml.risk_calibrator import predict_calibrated_risk_from_result
from backend.app.schemas import FactorExposure, SimulationResult
from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.agent_disagreement import calculate_agent_disagreement
from backend.app.services.confidence_engine import calculate_confidence_interval
from backend.app.services.dynamic_factor_updater import run_dynamic_factor_update
from backend.app.services.evidence_tracker import build_simulation_evidence
from backend.app.services.factor_mapper import map_factors
from backend.app.services.hidden_concentration import calculate_hidden_concentration
from backend.app.services.market_metrics import compute_market_metrics
from backend.app.services.risk_scoring import score_portfolio


def apply_dynamic_updates_to_exposures(
    base_exposures: list[FactorExposure],
    dynamic_update: dict,
) -> list[FactorExposure]:
    updated = []
    update_lookup = {}

    for ticker, ticker_updates in dynamic_update.get("ticker_updates", {}).items():
        for item in ticker_updates:
            update_lookup[(ticker, item["factor"])] = item

    for exposure in base_exposures:
        key = (exposure.ticker, exposure.factor)
        update = update_lookup.get(key)

        if update is None or update["adjustment"] <= 0:
            updated.append(exposure)
            continue

        evidence = list(exposure.evidence)
        evidence.append(
            (
                "Dynamic news adjustment applied: "
                f"base={update['base_score']}, dynamic={update['dynamic_score']}, "
                f"adjustment=+{update['adjustment']}."
            )
        )

        for narrative_evidence in update.get("narrative_evidence", []):
            display_name = narrative_evidence.get("display_name")
            adjustment = narrative_evidence.get("adjustment")
            reason = narrative_evidence.get("reason")
            evidence.append(
                f"News narrative '{display_name}' adjusted this factor by +{adjustment}: {reason}"
            )

        updated.append(
            FactorExposure(
                ticker=exposure.ticker,
                factor=exposure.factor,
                score=update["dynamic_score"],
                confidence=update["dynamic_confidence"],
                evidence=evidence,
            )
        )

    existing_keys = {(item.ticker, item.factor) for item in updated}

    for ticker, ticker_updates in dynamic_update.get("ticker_updates", {}).items():
        for item in ticker_updates:
            key = (ticker, item["factor"])

            if key in existing_keys or item["dynamic_score"] <= 0:
                continue

            if not item["exists_in_base_map"] and item["adjustment"] > 0:
                evidence = [
                    (
                        "Dynamic-only factor exposure created from news narrative: "
                        f"dynamic_score={item['dynamic_score']}, adjustment=+{item['adjustment']}."
                    )
                ]

                for narrative_evidence in item.get("narrative_evidence", []):
                    evidence.extend(narrative_evidence.get("evidence", [])[:2])

                updated.append(
                    FactorExposure(
                        ticker=ticker,
                        factor=item["factor"],
                        score=item["dynamic_score"],
                        confidence=item["dynamic_confidence"],
                        evidence=evidence,
                    )
                )

    return updated


def run_news_aware_simulation(
    portfolio,
    scenario,
    articles: list[dict],
    use_market_data: bool = True,
    run_ml_calibration: bool = True,
) -> dict:
    base_exposures = map_factors(portfolio, scenario)

    tickers = [holding.ticker for holding in portfolio.holdings]
    dynamic_update = run_dynamic_factor_update(
        articles=articles,
        tickers=tickers,
    )

    dynamic_exposures = apply_dynamic_updates_to_exposures(
        base_exposures=base_exposures,
        dynamic_update=dynamic_update,
    )

    market_metrics = None
    if use_market_data:
        market_metrics = compute_market_metrics(
            portfolio=portfolio,
            start="2024-01-01",
            benchmark="SPY",
        )

    agent_opinions = run_agent_debate(portfolio, scenario, dynamic_exposures)

    score, risk_level, factor_contributions, holding_risks = score_portfolio(
        portfolio=portfolio,
        scenario=scenario,
        exposures=dynamic_exposures,
        agent_opinions=agent_opinions,
        market_metrics=market_metrics,
    )

    confidence_interval = calculate_confidence_interval(
        score=score,
        portfolio=portfolio,
        exposures=dynamic_exposures,
        agent_opinions=agent_opinions,
        market_metrics=market_metrics,
    )

    hidden_concentration = calculate_hidden_concentration(
        portfolio=portfolio,
        exposures=dynamic_exposures,
    )

    evidence_items = build_simulation_evidence(
        portfolio=portfolio,
        scenario=scenario,
        exposures=dynamic_exposures,
        holding_risks=holding_risks,
        agent_opinions=agent_opinions,
        hidden_concentration=hidden_concentration,
        market_metrics=market_metrics,
    )

    agent_disagreement = calculate_agent_disagreement(agent_opinions)

    dominant_factors = list(factor_contributions.keys())
    most_vulnerable_holdings = [
        holding.ticker
        for holding in holding_risks
        if holding.risk_score >= 20
    ][:3]

    summary = (
        f"The news-aware simulation produced a {risk_level} vulnerability score of {score}/100 "
        f"under the '{scenario.name}' scenario. Dynamic news narratives adjusted factor exposures "
        f"for {len(dynamic_update.get('ticker_updates', {}))} tickers."
    )

    result = SimulationResult(
        portfolio_name=portfolio.name,
        scenario=scenario,
        vulnerability_score=score,
        risk_level=risk_level,
        dominant_factors=dominant_factors,
        most_vulnerable_holdings=most_vulnerable_holdings,
        holding_risks=holding_risks,
        factor_contributions=factor_contributions,
        agent_opinions=agent_opinions,
        summary=summary,
        disclaimer=(
            "Educational scenario analysis only. This is not financial advice, "
            "does not recommend buying or selling securities, and does not guarantee future returns."
        ),
        market_metrics=market_metrics,
        confidence_interval=confidence_interval,
        hidden_concentration=hidden_concentration,
        evidence_items=evidence_items,
        agent_disagreement=agent_disagreement,
    )

    ml_calibration = None
    if run_ml_calibration:
        try:
            ml_calibration = predict_calibrated_risk_from_result(result)
        except FileNotFoundError:
            ml_calibration = None

    return {
        "result": result.model_dump(mode="json"),
        "dynamic_factor_update": dynamic_update,
        "ml_calibration": ml_calibration,
        "news_adjusted": True,
    }
