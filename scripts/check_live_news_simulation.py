import json
from pathlib import Path

from backend.app.services.live_news import fetch_live_market_news_safe
from backend.app.main import load_sample_portfolio
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_generator import get_scenario
from backend.app.services.news_aware_simulation import run_news_aware_simulation


def main():
    tickers = ["NVDA", "MSFT", "AAPL", "SPY"]

    live_news = fetch_live_market_news_safe(
        tickers=tickers,
        query="AI",
        max_articles=5,
    )

    raw = load_sample_portfolio("ai_growth_sample")
    portfolio = normalize_portfolio(raw)
    scenario = get_scenario("ai_capex_slowdown")

    output = run_news_aware_simulation(
        portfolio=portfolio,
        scenario=scenario,
        articles=live_news["articles"],
        use_market_data=True,
        run_ml_calibration=True,
    )

    output["live_news"] = live_news

    output_path = Path("reports/json/live_news_simulation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("\\nRiskLens Alpha Live News Simulation")
    print("=" * 56)
    print(f"News status: {live_news['status']}")
    print(f"Source: {live_news['source']}")
    print(f"Articles: {live_news['article_count']}")

    for article in live_news["articles"][:3]:
        print(f"- {article['title']}")

    print("\\nSimulation:")
    print(f"Score: {output['result']['vulnerability_score']}/100")
    print(f"Risk level: {output['result']['risk_level']}")

    if output.get("ml_calibration"):
        print(f"ML calibrated score: {output['ml_calibration']['calibrated_score']}/100")

    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
