import json
from pathlib import Path

from backend.app.services.news_narrative_extractor import extract_batch_news_narratives


def main():
    articles = [
        {
            "title": "NVDA and AMD fall after new China AI chip export controls",
            "summary": "Investors worry that advanced accelerator shipments to China could be limited by new licensing restrictions.",
            "tickers": ["NVDA", "AMD"],
        },
        {
            "title": "Treasury yields jump as inflation data pressures rate cut hopes",
            "summary": "Technology and growth stocks declined as traders priced in a higher-for-longer policy path.",
            "tickers": ["QQQ", "MSFT"],
        },
        {
            "title": "Microsoft warns cloud customers continue to optimize spending",
            "summary": "Enterprise cloud growth expectations softened after cautious commentary from software buyers.",
            "tickers": ["MSFT"],
        },
    ]

    results = extract_batch_news_narratives(articles)

    output_path = Path("reports/json/news_narratives.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\nRiskLens Alpha News Narrative Extraction")
    print("=" * 56)

    for result in results:
        print(f"\nNarrative: {result['display_name']}")
        print(f"Label: {result['narrative']}")
        print(f"Severity: {result['severity']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Tickers: {', '.join(result['affected_tickers'][:8])}")
        print(f"Factors: {', '.join(result['affected_factors'])}")

    print(f"\nSaved extracted narratives to: {output_path}")


if __name__ == "__main__":
    main()
