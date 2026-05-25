from backend.app.services.live_news import (
    build_fallback_news_articles,
    fetch_live_market_news_safe,
    normalize_tickers,
)


def test_normalize_tickers_from_string():
    assert normalize_tickers("nvda, msft AAPL") == ["NVDA", "MSFT", "AAPL"]


def test_build_fallback_news_articles_shape():
    articles = build_fallback_news_articles(["NVDA", "MSFT"], query="AI")

    assert len(articles) == 1
    assert articles[0]["tickers"] == ["NVDA", "MSFT"]
    assert "title" in articles[0]
    assert "summary" in articles[0]


def test_fetch_live_market_news_safe_returns_shape():
    result = fetch_live_market_news_safe(
        tickers=["NVDA"],
        query="AI",
        max_articles=2,
    )

    assert "status" in result
    assert "articles" in result
    assert "article_count" in result
    assert result["article_count"] >= 1
