from sqlalchemy.orm import Session

from backend.app.models import AlertModel


def find_duplicate_unread_alert(
    db: Session,
    portfolio_id: int,
    alert_type: str,
    scenario_id: str | None = None,
    ticker: str | None = None,
    threshold: float | None = None,
) -> AlertModel | None:
    query = db.query(AlertModel).filter(
        AlertModel.portfolio_id == portfolio_id,
        AlertModel.alert_type == alert_type,
        AlertModel.is_read.is_(False),
    )

    if scenario_id is None:
        query = query.filter(AlertModel.scenario_id.is_(None))
    else:
        query = query.filter(AlertModel.scenario_id == scenario_id)

    if ticker is None:
        query = query.filter(AlertModel.ticker.is_(None))
    else:
        query = query.filter(AlertModel.ticker == ticker)

    if threshold is None:
        query = query.filter(AlertModel.threshold.is_(None))
    else:
        query = query.filter(AlertModel.threshold == threshold)

    return query.first()


def create_alert(
    db: Session,
    portfolio_id: int,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    scenario_id: str | None = None,
    ticker: str | None = None,
    value: float | None = None,
    threshold: float | None = None,
) -> AlertModel:
    alert = AlertModel(
        portfolio_id=portfolio_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        scenario_id=scenario_id,
        ticker=ticker,
        value=value,
        threshold=threshold,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def create_alert_if_missing(
    db: Session,
    portfolio_id: int,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    scenario_id: str | None = None,
    ticker: str | None = None,
    value: float | None = None,
    threshold: float | None = None,
) -> tuple[AlertModel, bool]:
    existing = find_duplicate_unread_alert(
        db=db,
        portfolio_id=portfolio_id,
        alert_type=alert_type,
        scenario_id=scenario_id,
        ticker=ticker,
        threshold=threshold,
    )

    if existing is not None:
        return existing, False

    alert = create_alert(
        db=db,
        portfolio_id=portfolio_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        scenario_id=scenario_id,
        ticker=ticker,
        value=value,
        threshold=threshold,
    )

    return alert, True


def list_alerts(
    db: Session,
    portfolio_id: int | None = None,
    unread_only: bool = False,
    limit: int = 100,
) -> list[AlertModel]:
    query = db.query(AlertModel)

    if portfolio_id is not None:
        query = query.filter(AlertModel.portfolio_id == portfolio_id)

    if unread_only:
        query = query.filter(AlertModel.is_read.is_(False))

    return (
        query.order_by(AlertModel.created_at.desc())
        .limit(limit)
        .all()
    )


def mark_alert_read(db: Session, alert_id: int) -> AlertModel | None:
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()

    if alert is None:
        return None

    alert.is_read = True
    db.commit()
    db.refresh(alert)

    return alert


def delete_alert(db: Session, alert_id: int) -> bool:
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()

    if alert is None:
        return False

    db.delete(alert)
    db.commit()

    return True


def alert_to_dict(alert: AlertModel) -> dict:
    return {
        "id": alert.id,
        "portfolio_id": alert.portfolio_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "message": alert.message,
        "scenario_id": alert.scenario_id,
        "ticker": alert.ticker,
        "value": alert.value,
        "threshold": alert.threshold,
        "is_read": alert.is_read,
        "created_at": alert.created_at.isoformat(),
    }
