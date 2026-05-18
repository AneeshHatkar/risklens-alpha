from sqlalchemy.orm import Session

from backend.app.models import PortfolioModel
from backend.app.services.alert_repository import create_alert_if_missing
from backend.app.services.portfolio_repository import get_portfolio_by_id, list_portfolios


DEFAULT_SCENARIOS = [
    "ai_capex_slowdown",
    "higher_for_longer_rates",
]


def severity_from_score(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 75:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def check_single_portfolio_alerts(
    db: Session,
    portfolio: PortfolioModel,
    risk_threshold: int = 75,
    hidden_concentration_threshold: int = 80,
    volatility_threshold: float = 0.35,
    correlation_threshold: float = 0.70,
) -> list:
    from backend.app.services.job_manager import run_database_portfolio_simulation_for_job

    created = []

    for scenario_id in DEFAULT_SCENARIOS:
        result = run_database_portfolio_simulation_for_job(
            portfolio_model=portfolio,
            scenario_id=scenario_id,
        )

        if result.vulnerability_score >= risk_threshold:
            alert, was_created = create_alert_if_missing(
                db=db,
                portfolio_id=portfolio.id,
                alert_type="risk_score_threshold",
                severity=severity_from_score(result.vulnerability_score),
                title=f"Risk score crossed {risk_threshold}",
                message=(
                    f"{portfolio.name} scored {result.vulnerability_score}/100 "
                    f"under {result.scenario.name}."
                ),
                scenario_id=scenario_id,
                value=float(result.vulnerability_score),
                threshold=float(risk_threshold),
            )
            if was_created:
                created.append(alert)

        hidden = result.hidden_concentration or {}
        hidden_score = hidden.get("score")

        if hidden_score is not None and hidden_score >= hidden_concentration_threshold:
            alert, was_created = create_alert_if_missing(
                db=db,
                portfolio_id=portfolio.id,
                alert_type="hidden_concentration_threshold",
                severity=severity_from_score(hidden_score),
                title=f"Hidden concentration crossed {hidden_concentration_threshold}",
                message=(
                    f"{portfolio.name} has hidden concentration score "
                    f"{hidden_score}/100."
                ),
                scenario_id=scenario_id,
                value=float(hidden_score),
                threshold=float(hidden_concentration_threshold),
            )
            if was_created:
                created.append(alert)

        market_metrics = result.market_metrics or {}
        portfolio_metrics = market_metrics.get("portfolio_metrics", {})

        volatility = portfolio_metrics.get("portfolio_volatility")
        if volatility is not None and volatility >= volatility_threshold:
            alert, was_created = create_alert_if_missing(
                db=db,
                portfolio_id=portfolio.id,
                alert_type="volatility_threshold",
                severity="medium",
                title=f"Portfolio volatility crossed {volatility_threshold}",
                message=(
                    f"{portfolio.name} has portfolio volatility {volatility}, "
                    f"above threshold {volatility_threshold}."
                ),
                scenario_id=scenario_id,
                value=float(volatility),
                threshold=float(volatility_threshold),
            )
            if was_created:
                created.append(alert)

        correlation = portfolio_metrics.get("average_pairwise_correlation")
        if correlation is not None and correlation >= correlation_threshold:
            alert, was_created = create_alert_if_missing(
                db=db,
                portfolio_id=portfolio.id,
                alert_type="correlation_threshold",
                severity="medium",
                title=f"Correlation crossed {correlation_threshold}",
                message=(
                    f"{portfolio.name} has average pairwise correlation {correlation}, "
                    f"above threshold {correlation_threshold}."
                ),
                scenario_id=scenario_id,
                value=float(correlation),
                threshold=float(correlation_threshold),
            )
            if was_created:
                created.append(alert)

    return created


def check_alerts_for_portfolios(
    db: Session,
    portfolio_id: int | None = None,
    risk_threshold: int = 75,
    hidden_concentration_threshold: int = 80,
    volatility_threshold: float = 0.35,
    correlation_threshold: float = 0.70,
) -> dict:
    if portfolio_id is not None:
        portfolio = get_portfolio_by_id(db, portfolio_id)
        portfolios = [portfolio] if portfolio is not None else []
    else:
        portfolios = list_portfolios(db)

    created_alerts = []

    for portfolio in portfolios:
        created_alerts.extend(
            check_single_portfolio_alerts(
                db=db,
                portfolio=portfolio,
                risk_threshold=risk_threshold,
                hidden_concentration_threshold=hidden_concentration_threshold,
                volatility_threshold=volatility_threshold,
                correlation_threshold=correlation_threshold,
            )
        )

    return {
        "portfolio_count": len(portfolios),
        "created_alert_count": len(created_alerts),
        "alert_ids": [alert.id for alert in created_alerts],
    }
