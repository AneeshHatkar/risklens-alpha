from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.database import SessionLocal
from backend.app.services.market_metrics import compute_market_metrics
from backend.app.services.portfolio_repository import (
    list_portfolios,
    portfolio_model_to_schema,
)
from backend.app.services.scenario_generator import SCENARIOS
from backend.app.services.timeline_repository import save_timeline_point
from backend.app.main import run_simulation


scheduler = BackgroundScheduler()


def refresh_saved_portfolio_risk_timelines(db: Session | None = None) -> dict:
    owns_session = db is None

    if db is None:
        db = SessionLocal()

    try:
        portfolios = list_portfolios(db)
        created_points = 0

        for portfolio_model in portfolios:
            # Use the most important scenarios for timeline refresh.
            for scenario_id in ["ai_capex_slowdown", "higher_for_longer_rates"]:
                result = run_database_portfolio_simulation_for_job(
                    portfolio_model=portfolio_model,
                    scenario_id=scenario_id,
                )

                save_timeline_point(
                    db=db,
                    portfolio_id=portfolio_model.id,
                    scenario_id=scenario_id,
                    result=result,
                    source="background_refresh",
                )
                created_points += 1

        return {
            "portfolio_count": len(portfolios),
            "created_points": created_points,
        }

    finally:
        if owns_session:
            db.close()


def run_database_portfolio_simulation_for_job(portfolio_model, scenario_id: str):
    # Reuse the core simulation components without needing portfolio_id from sample JSON.
    from backend.app.services.agent_debate import run_agent_debate
    from backend.app.services.confidence_engine import calculate_confidence_interval
    from backend.app.services.evidence_tracker import build_simulation_evidence
    from backend.app.services.factor_mapper import map_factors
    from backend.app.services.hidden_concentration import calculate_hidden_concentration
    from backend.app.services.risk_scoring import score_portfolio
    from backend.app.schemas import SimulationResult

    portfolio = portfolio_model_to_schema(portfolio_model)
    scenario = SCENARIOS[scenario_id]

    market_metrics = None
    settings = get_settings()

    try:
        market_metrics = compute_market_metrics(
            portfolio=portfolio,
            start=settings.market_data_start_date,
            benchmark=settings.market_data_benchmark,
        )
    except Exception:
        market_metrics = None

    exposures = map_factors(portfolio, scenario)
    agents = run_agent_debate(portfolio, scenario, exposures)

    score, level, factor_contributions, holding_risks = score_portfolio(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        agent_opinions=agents,
        market_metrics=market_metrics,
    )

    dominant_factors = list(factor_contributions.keys())
    most_vulnerable = [
        holding.ticker for holding in holding_risks
        if holding.risk_score >= 20
    ][:3]

    confidence_interval = calculate_confidence_interval(
        score=score,
        portfolio=portfolio,
        exposures=exposures,
        agent_opinions=agents,
        market_metrics=market_metrics,
    )

    hidden_concentration = calculate_hidden_concentration(
        portfolio=portfolio,
        exposures=exposures,
    )

    evidence_items = build_simulation_evidence(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        holding_risks=holding_risks,
        agent_opinions=agents,
        hidden_concentration=hidden_concentration,
        market_metrics=market_metrics,
    )

    summary = (
        f"The portfolio has a {level} simulated vulnerability score of {score}/100 "
        f"under the '{scenario.name}' scenario."
    )

    return SimulationResult(
        portfolio_name=portfolio.name,
        scenario=scenario,
        vulnerability_score=score,
        risk_level=level,
        dominant_factors=dominant_factors,
        most_vulnerable_holdings=most_vulnerable,
        holding_risks=holding_risks,
        factor_contributions=factor_contributions,
        agent_opinions=agents,
        summary=summary,
        disclaimer=(
            "Educational scenario analysis only. This is not financial advice, "
            "does not recommend buying or selling securities, and does not guarantee future returns."
        ),
        market_metrics=market_metrics,
        confidence_interval=confidence_interval,
        hidden_concentration=hidden_concentration,
        evidence_items=evidence_items,
    )


def run_market_refresh_job() -> dict:
    settings = get_settings()

    try:
        details = refresh_saved_portfolio_risk_timelines()
        return {
            "job_name": "market_refresh",
            "status": "success",
            "message": "Saved portfolio risk timelines refreshed.",
            "details": details,
        }
    except Exception as error:
        return {
            "job_name": "market_refresh",
            "status": "failed",
            "message": str(error),
            "details": {
                "market_data_provider": settings.market_data_provider,
            },
        }


def start_scheduler() -> dict:
    settings = get_settings()

    if scheduler.running:
        return {
            "status": "already_running",
            "message": "Background scheduler is already running.",
        }

    scheduler.add_job(
        run_market_refresh_job,
        "interval",
        minutes=settings.market_refresh_interval_minutes,
        id="market_refresh",
        replace_existing=True,
    )

    scheduler.start()

    return {
        "status": "started",
        "message": "Background scheduler started.",
        "jobs": get_scheduler_status()["jobs"],
    }


def stop_scheduler() -> dict:
    if not scheduler.running:
        return {
            "status": "not_running",
            "message": "Background scheduler is not running.",
        }

    scheduler.shutdown(wait=False)

    return {
        "status": "stopped",
        "message": "Background scheduler stopped.",
    }


def get_scheduler_status() -> dict:
    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in scheduler.get_jobs()
        ],
    }
