from __future__ import annotations

from statistics import mean, pstdev


def safe_z_score(value: float, values: list[float]) -> float:
    if len(values) < 2:
        return 0.0

    avg = mean(values)
    std = pstdev(values)

    if std == 0:
        return 0.0

    return round((value - avg) / std, 4)


def severity_from_z_score(z_score: float) -> str:
    abs_z = abs(z_score)

    if abs_z >= 2.5:
        return "high"
    if abs_z >= 1.5:
        return "medium"
    return "low"


def detect_series_anomalies(
    points: list[dict],
    field: str,
    min_history: int = 3,
    z_threshold: float = 1.5,
) -> list[dict]:
    anomalies = []

    chronological = sorted(points, key=lambda item: item["created_at"])

    history = []

    for point in chronological:
        value = point.get(field)

        if value is None:
            continue

        value = float(value)

        if len(history) >= min_history:
            z_score = safe_z_score(value, history)

            if abs(z_score) >= z_threshold:
                anomalies.append(
                    {
                        "timeline_point_id": point["id"],
                        "portfolio_id": point["portfolio_id"],
                        "scenario_id": point["scenario_id"],
                        "scenario_name": point["scenario_name"],
                        "field": field,
                        "value": value,
                        "z_score": z_score,
                        "severity": severity_from_z_score(z_score),
                        "created_at": point["created_at"],
                        "message": build_anomaly_message(
                            field=field,
                            value=value,
                            z_score=z_score,
                            scenario_name=point["scenario_name"],
                        ),
                    }
                )

        history.append(value)

    return anomalies


def detect_jump_anomalies(
    points: list[dict],
    field: str,
    jump_threshold: float,
) -> list[dict]:
    anomalies = []

    chronological = sorted(points, key=lambda item: item["created_at"])

    previous = None

    for point in chronological:
        value = point.get(field)

        if value is None:
            continue

        value = float(value)

        if previous is not None:
            delta = value - previous

            if abs(delta) >= jump_threshold:
                anomalies.append(
                    {
                        "timeline_point_id": point["id"],
                        "portfolio_id": point["portfolio_id"],
                        "scenario_id": point["scenario_id"],
                        "scenario_name": point["scenario_name"],
                        "field": field,
                        "value": value,
                        "previous_value": previous,
                        "delta": round(delta, 4),
                        "severity": "high" if abs(delta) >= jump_threshold * 1.5 else "medium",
                        "created_at": point["created_at"],
                        "message": (
                            f"{field} changed by {delta:+.2f} for "
                            f"{point['scenario_name']}."
                        ),
                    }
                )

        previous = value

    return anomalies


def build_anomaly_message(
    field: str,
    value: float,
    z_score: float,
    scenario_name: str,
) -> str:
    direction = "above" if z_score > 0 else "below"

    return (
        f"{field} is unusually {direction} recent history for {scenario_name}: "
        f"value={value:.2f}, z_score={z_score:.2f}."
    )


def detect_risk_timeline_anomalies(points: list[dict]) -> dict:
    risk_score_anomalies = detect_series_anomalies(
        points=points,
        field="vulnerability_score",
        min_history=3,
        z_threshold=1.5,
    )

    hidden_concentration_anomalies = detect_series_anomalies(
        points=points,
        field="hidden_concentration_score",
        min_history=3,
        z_threshold=1.5,
    )

    confidence_width_points = []

    for point in points:
        lower = point.get("confidence_lower")
        upper = point.get("confidence_upper")

        confidence_width = None

        if lower is not None and upper is not None:
            confidence_width = float(upper) - float(lower)

        confidence_width_points.append(
            {
                **point,
                "confidence_width": confidence_width,
            }
        )

    confidence_width_anomalies = detect_series_anomalies(
        points=confidence_width_points,
        field="confidence_width",
        min_history=3,
        z_threshold=1.5,
    )

    jump_anomalies = []
    jump_anomalies.extend(
        detect_jump_anomalies(
            points=points,
            field="vulnerability_score",
            jump_threshold=10,
        )
    )
    jump_anomalies.extend(
        detect_jump_anomalies(
            points=points,
            field="hidden_concentration_score",
            jump_threshold=12,
        )
    )

    all_anomalies = (
        risk_score_anomalies
        + hidden_concentration_anomalies
        + confidence_width_anomalies
        + jump_anomalies
    )

    high_count = sum(1 for item in all_anomalies if item["severity"] == "high")
    medium_count = sum(1 for item in all_anomalies if item["severity"] == "medium")

    return {
        "point_count": len(points),
        "anomaly_count": len(all_anomalies),
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": sum(1 for item in all_anomalies if item["severity"] == "low"),
        "anomalies": sorted(
            all_anomalies,
            key=lambda item: (item["created_at"], item["field"]),
            reverse=True,
        ),
        "summary": build_anomaly_summary(
            point_count=len(points),
            anomaly_count=len(all_anomalies),
            high_count=high_count,
            medium_count=medium_count,
        ),
    }


def build_anomaly_summary(
    point_count: int,
    anomaly_count: int,
    high_count: int,
    medium_count: int,
) -> str:
    if point_count < 4:
        return (
            f"Only {point_count} timeline points are available. "
            "More history is needed for reliable anomaly detection."
        )

    if anomaly_count == 0:
        return f"No risk timeline anomalies detected across {point_count} timeline points."

    return (
        f"Detected {anomaly_count} risk timeline anomalies across {point_count} points "
        f"({high_count} high, {medium_count} medium)."
    )
