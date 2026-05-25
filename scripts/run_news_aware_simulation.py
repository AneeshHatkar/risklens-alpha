import json
from pathlib import Path

from backend.app.main import load_sample_portfolio
from backend.app.services.news_aware_simulation import run_news_aware_simulation
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_generator import get_scenario


def main():
    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)
    scenario = get_scenario("ai_capex_slowdown")

    articles = [
        {
            "title": "NVDA and AMD fall after new China AI chip export controls",
            "summary": "Investors worry that advanced accelerator shipments to China could be limited by new licensing restrictions.",
            "tickers": ["NVDA", "AMD"],
        },
        {
            "title": "Cloud giants slow AI data center spending after aggressive capex buildout",
            "summary": "Markets reassessed expectations for GPU demand, cloud AI infrastructure, and monetization timelines.",
            "tickers": ["NVDA", "MSFT", "AMZN"],
        },
    ]

    result = run_news_aware_simulation(
        portfolio=portfolio,
        scenario=scenario,
        articles=articles,
        use_market_data=True,
        run_ml_calibration=True,
    )

    output_path = Path("reports/json/news_aware_simulation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    simulation = result["result"]

    print("\nRiskLens Alpha News-Aware Simulation")
    print("=" * 56)
    print(f"Portfolio: {simulation['portfolio_name']}")
    print(f"Scenario: {simulation['scenario']['name']}")
    print(f"News-adjusted score: {simulation['vulnerability_score']}/100")
    print(f"Risk level: {simulation['risk_level']}")
    print(f"Dynamic narratives: {result['dynamic_factor_update']['narrative_count']}")

    if result["ml_calibration"]:
        print("\nML Calibration:")
        print(f"- calibrated_score: {result['ml_calibration']['calibrated_score']}")
        print(f"- calibrated_level: {result['ml_calibration']['calibrated_level']}")
        print(f"- severe_probability: {result['ml_calibration']['severe_probability']}")

    print("\nDynamic factor summary:")
    print(result["dynamic_factor_update"]["summary"])

    print(f"\nSaved news-aware simulation to: {output_path}")


if __name__ == "__main__":
    main()
