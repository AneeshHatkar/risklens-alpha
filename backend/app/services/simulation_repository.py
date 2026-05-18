import json

from sqlalchemy.orm import Session

from backend.app.models import SimulationRunModel
from backend.app.schemas import SimulationResult


def save_simulation_run(
    db: Session,
    portfolio_id: int,
    scenario_id: str,
    result: SimulationResult,
) -> SimulationRunModel:
    run = SimulationRunModel(
        portfolio_id=portfolio_id,
        scenario_id=scenario_id,
        scenario_name=result.scenario.name,
        vulnerability_score=result.vulnerability_score,
        risk_level=result.risk_level,
        summary=result.summary,
        result_json=json.dumps(result.model_dump(mode="json"), indent=2),
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def list_simulation_runs(db: Session, portfolio_id: int | None = None) -> list[SimulationRunModel]:
    query = db.query(SimulationRunModel)

    if portfolio_id is not None:
        query = query.filter(SimulationRunModel.portfolio_id == portfolio_id)

    return query.order_by(SimulationRunModel.created_at.desc()).all()


def get_simulation_run(db: Session, run_id: int) -> SimulationRunModel | None:
    return (
        db.query(SimulationRunModel)
        .filter(SimulationRunModel.id == run_id)
        .first()
    )


def simulation_run_summary(run: SimulationRunModel) -> dict:
    return {
        "id": run.id,
        "portfolio_id": run.portfolio_id,
        "scenario_id": run.scenario_id,
        "scenario_name": run.scenario_name,
        "vulnerability_score": run.vulnerability_score,
        "risk_level": run.risk_level,
        "created_at": run.created_at.isoformat(),
    }


def simulation_run_detail(run: SimulationRunModel) -> dict:
    return {
        **simulation_run_summary(run),
        "summary": run.summary,
        "result": json.loads(run.result_json),
    }
