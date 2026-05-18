from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.app.schemas import SimulationResult


def get_template_environment() -> Environment:
    template_dir = Path(__file__).resolve().parents[1] / "templates"

    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_risk_report_html(
    result: SimulationResult,
    output_path: str = "reports/html/latest_report.html",
    title: str = "RiskLens Alpha Risk Report",
) -> Path:
    env = get_template_environment()
    template = env.get_template("risk_report.html")

    html = template.render(
        title=title,
        result=result,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")

    return path


def render_risk_report_from_json(
    json_path: str,
    output_path: str = "reports/html/latest_report.html",
) -> Path:
    import json

    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    result = SimulationResult.model_validate(data)

    return render_risk_report_html(
        result=result,
        output_path=output_path,
    )
