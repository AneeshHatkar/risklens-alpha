import json
from pathlib import Path

from backend.app.services.dynamic_factor_updater import run_dynamic_factor_update


def main():
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

    result = run_dynamic_factor_update(
        articles=articles,
        tickers=["NVDA", "MSFT", "AMD", "SMH"],
    )

    output_path = Path("reports/json/dynamic_factor_update.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\nRiskLens Alpha Dynamic Factor Update")
    print("=" * 56)
    print(f"Tickers: {', '.join(result['tickers'])}")
    print(f"Narratives detected: {result['narrative_count']}")
    print("\nSummary:")
    print(result["summary"])

    print("\nTop Dynamic Updates:")
    for ticker, updates in result["ticker_updates"].items():
        print(f"\n{ticker}")
        top_updates = [item for item in updates if item["adjustment"] > 0][:5]
        if not top_updates:
            print("- No dynamic adjustments")
            continue

        for item in top_updates:
            print(
                f"- {item['factor']}: base={item['base_score']}, "
                f"dynamic={item['dynamic_score']}, adjustment=+{item['adjustment']}"
            )

    print(f"\nSaved dynamic factor update to: {output_path}")


if __name__ == "__main__":
    main()
