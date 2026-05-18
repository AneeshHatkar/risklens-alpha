from backend.app.main import run_simulation
from backend.app.services.pdf_report import render_risk_report_pdf


def main():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=True,
    )

    output_path = render_risk_report_pdf(
        result=result,
        html_output_path="reports/html/latest_report.html",
        pdf_output_path="reports/pdf/latest_report.pdf",
    )

    print(f"RiskLens Alpha PDF report generated: {output_path}")


if __name__ == "__main__":
    main()
