from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


YAHOO_FINANCE_NEWS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={tickers}&region=US&lang=en-US"


def clean_text(value: str | None) -> str:
    if not value:
        return ""

    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_tickers(tickers: list[str] | str | None) -> list[str]:
    if tickers is None:
        return []

    if isinstance(tickers, str):
        parts = re.split(r"[,\s]+", tickers)
    else:
        parts = tickers

    clean = []

    for ticker in parts:
        item = ticker.strip().upper()
        if item and item not in clean:
            clean.append(item)

    return clean


def fetch_yahoo_finance_news(
    tickers: list[str] | str,
    max_articles: int = 10,
    timeout: int = 10,
) -> list[dict]:
    clean_tickers = normalize_tickers(tickers)

    if not clean_tickers:
        return []

    encoded = quote_plus(",".join(clean_tickers))
    url = YAHOO_FINANCE_NEWS_URL.format(tickers=encoded)

    request = Request(
        url,
        headers={
            "User-Agent": "RiskLensAlpha/1.0 educational research project",
        },
    )

    with urlopen(request, timeout=timeout) as response:
        raw = response.read()

    root = ET.fromstring(raw)
    articles = []

    for item in root.findall("./channel/item")[:max_articles]:
        title = clean_text(item.findtext("title"))
        summary = clean_text(item.findtext("description"))
        link = clean_text(item.findtext("link"))
        published = clean_text(item.findtext("pubDate"))

        if not title:
            continue

        articles.append(
            {
                "title": title,
                "summary": summary,
                "url": link,
                "source": "Yahoo Finance RSS",
                "published_at": published,
                "tickers": clean_tickers,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return articles


def fetch_live_market_news(
    tickers: list[str] | str,
    query: str | None = None,
    max_articles: int = 10,
) -> dict:
    clean_tickers = normalize_tickers(tickers)

    articles = fetch_yahoo_finance_news(
        tickers=clean_tickers,
        max_articles=max_articles,
    )

    if query:
        query_lower = query.lower()
        filtered = [
            article
            for article in articles
            if query_lower in article.get("title", "").lower()
            or query_lower in article.get("summary", "").lower()
        ]

        if filtered:
            articles = filtered

    return {
        "tickers": clean_tickers,
        "query": query,
        "article_count": len(articles),
        "articles": articles,
        "source": "Yahoo Finance RSS",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def build_fallback_news_articles(tickers: list[str] | str, query: str | None = None) -> list[dict]:
    clean_tickers = normalize_tickers(tickers)
    joined = ", ".join(clean_tickers) if clean_tickers else "the selected portfolio"

    topic = query or "market risk"

    return [
        {
            "title": f"Market update for {joined}: {topic}",
            "summary": (
                f"Fallback article generated because live news was unavailable. "
                f"The update discusses {topic}, market beta, valuation pressure, "
                f"earnings expectations, and risk sentiment for {joined}."
            ),
            "url": "",
            "source": "RiskLens fallback",
            "published_at": "",
            "tickers": clean_tickers,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    ]


def fetch_live_market_news_safe(
    tickers: list[str] | str,
    query: str | None = None,
    max_articles: int = 10,
) -> dict:
    clean_tickers = normalize_tickers(tickers)

    try:
        result = fetch_live_market_news(
            tickers=clean_tickers,
            query=query,
            max_articles=max_articles,
        )

        if result["article_count"] > 0:
            result["status"] = "success"
            result["warnings"] = []
            return result

        fallback = build_fallback_news_articles(clean_tickers, query=query)

        return {
            "tickers": clean_tickers,
            "query": query,
            "article_count": len(fallback),
            "articles": fallback,
            "source": "fallback",
            "status": "fallback",
            "warnings": ["No live news articles returned. Used fallback article."],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as error:
        fallback = build_fallback_news_articles(clean_tickers, query=query)

        return {
            "tickers": clean_tickers,
            "query": query,
            "article_count": len(fallback),
            "articles": fallback,
            "source": "fallback",
            "status": "fallback",
            "warnings": [f"Live news fetch failed: {error}"],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
