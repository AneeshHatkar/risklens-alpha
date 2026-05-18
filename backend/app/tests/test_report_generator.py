from pathlib import Path

from backend.app.main import run_simulation
from backend.app.services.report_generator import render_risk_report_html


def test_render_risk_report_html_creates_file(tmp_path):
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    output_path = tmp_path / "risk_report.html"

    rendered = render_risk_report_html(
        result=result,
        output_path=str(output_path),
    )

    assert rendered.exists()

    html = rendered.read_text(encoding="utf-8")

    assert "RiskLens Alpha Risk Report" in html
    assert "AI Infrastructure Spending Slowdown" in html
    assert "Evidence Table" in html
    assert "not financial advice" in html.lower()


def test_report_contains_hidden_concentration_and_agent_debate(tmp_path):
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    output_path = tmp_path / "risk_report.html"
    render_risk_report_html(result=result, output_path=str(output_path))

    html = output_path.read_text(encoding="utf-8")

    assert "Hidden Concentration Analysis" in html
    assert "Multi-Agent Risk Debate" in html
    assert "Sector Agent" in html
