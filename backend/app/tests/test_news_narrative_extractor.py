from backend.app.services.news_narrative_extractor import (
    extract_batch_news_narratives,
    extract_news_narrative,
    extract_tickers_from_text,
    load_narrative_taxonomy,
)


def test_load_narrative_taxonomy():
    taxonomy = load_narrative_taxonomy()

    assert "ai_capex_slowdown" in taxonomy
    assert "semiconductor_export_restriction" in taxonomy
    assert "affected_factors" in taxonomy["ai_capex_slowdown"]


def test_extract_tickers_from_text():
    tickers = extract_tickers_from_text("NVDA and MSFT fell while SPY was flat.")

    assert "NVDA" in tickers
    assert "MSFT" in tickers
    assert "SPY" in tickers


def test_extract_news_narrative_returns_structured_result():
    result = extract_news_narrative(
        title="NVDA falls after new China chip export restrictions",
        summary="Investors worry that AI accelerator sales could be limited.",
        provided_tickers=["NVDA"],
    )

    assert "narrative" in result
    assert "affected_tickers" in result
    assert "affected_factors" in result
    assert "severity" in result
    assert "evidence" in result
    assert "NVDA" in result["affected_tickers"]
    assert 0 <= result["severity"] <= 1


def test_extract_batch_news_narratives():
    results = extract_batch_news_narratives(
        [
            {
                "title": "Treasury yields rise and growth stocks fall",
                "summary": "Markets price in a higher-for-longer rate path.",
                "tickers": ["QQQ"],
            },
            {
                "title": "Cloud spending optimization pressures software stocks",
                "summary": "Enterprise customers are delaying cloud migration contracts.",
                "tickers": ["MSFT"],
            },
        ]
    )

    assert len(results) == 2
    assert all("narrative" in item for item in results)
