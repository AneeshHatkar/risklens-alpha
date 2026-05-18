from backend.app.main import run_simulation
from backend.app.services.report_generator import render_risk_report_html


def main():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=True,
    )

    output_path = render_risk_report_html(
        result=result,
        output_path="reports/html/latest_report.html",
    )

    print(f"RiskLens Alpha HTML report generated: {output_path}")


if __name__ == "__main__":
    main()
