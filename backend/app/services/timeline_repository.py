from sqlalchemy.orm import Session

from backend.app.models import RiskTimelinePointModel
from backend.app.schemas import SimulationResult


def save_timeline_point(
    db: Session,
    portfolio_id: int,
    scenario_id: str,
    result: SimulationResult,
    source: str = "simulation",
) -> RiskTimelinePointModel:
    confidence = result.confidence_interval or {}
    hidden = result.hidden_concentration or {}

    point = RiskTimelinePointModel(
        portfolio_id=portfolio_id,
        scenario_id=scenario_id,
        scenario_name=result.scenario.name,
        vulnerability_score=result.vulnerability_score,
        risk_level=result.risk_level,
        hidden_concentration_score=hidden.get("score"),
        confidence_lower=confidence.get("lower"),
        confidence_upper=confidence.get("upper"),
        source=source,
    )

    db.add(point)
    db.commit()
    db.refresh(point)

    return point


def list_timeline_points(
    db: Session,
    portfolio_id: int,
    scenario_id: str | None = None,
    limit: int = 100,
) -> list[RiskTimelinePointModel]:
    query = db.query(RiskTimelinePointModel).filter(
        RiskTimelinePointModel.portfolio_id == portfolio_id
    )

    if scenario_id:
        query = query.filter(RiskTimelinePointModel.scenario_id == scenario_id)

    return (
        query.order_by(RiskTimelinePointModel.created_at.desc())
        .limit(limit)
        .all()
    )


def timeline_point_to_dict(point: RiskTimelinePointModel) -> dict:
    return {
        "id": point.id,
        "portfolio_id": point.portfolio_id,
        "scenario_id": point.scenario_id,
        "scenario_name": point.scenario_name,
        "vulnerability_score": point.vulnerability_score,
        "risk_level": point.risk_level,
        "hidden_concentration_score": point.hidden_concentration_score,
        "confidence_lower": point.confidence_lower,
        "confidence_upper": point.confidence_upper,
        "source": point.source,
        "created_at": point.created_at.isoformat(),
    }
