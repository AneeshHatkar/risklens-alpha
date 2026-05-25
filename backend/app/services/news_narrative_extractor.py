from __future__ import annotations

import json
import re
from pathlib import Path

from backend.app.ml.narrative_classifier import predict_narrative


TAXONOMY_PATH = "backend/app/data/narrative_taxonomy.json"


def load_narrative_taxonomy(path: str = TAXONOMY_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def extract_tickers_from_text(text: str, known_tickers: list[str] | None = None) -> list[str]:
    if known_tickers is None:
        known_tickers = [
            "NVDA", "AMD", "SMH", "MSFT", "AAPL", "GOOGL", "AMZN", "TSLA",
            "SPY", "QQQ", "XLK", "XLF", "XLE", "XLY", "KRE", "IWM", "VTI",
            "CRM", "NOW", "ASML", "TSM"
        ]

    upper_text = text.upper()
    found = []

    for ticker in known_tickers:
        pattern = rf"\b{re.escape(ticker)}\b"
        if re.search(pattern, upper_text):
            found.append(ticker)

    return found


def keyword_severity_adjustment(text: str, severity_keywords: list[str]) -> float:
    lower_text = text.lower()
    matches = 0

    for keyword in severity_keywords:
        if keyword.lower() in lower_text:
            matches += 1

    # Cap adjustment so one article does not over-amplify severity.
    return min(0.18, matches * 0.03)


def estimate_narrative_severity(
    text: str,
    base_severity: float,
    confidence: float,
    severity_keywords: list[str],
) -> float:
    adjustment = keyword_severity_adjustment(text, severity_keywords)

    # Small confidence contribution. Current model confidence is low due to small dataset,
    # so do not let confidence dominate severity yet.
    confidence_adjustment = min(0.08, confidence * 0.12)

    severity = base_severity + adjustment + confidence_adjustment

    return round(min(1.0, max(0.0, severity)), 4)


def build_evidence_snippets(title: str, summary: str, label: str, taxonomy_entry: dict) -> list[str]:
    snippets = []

    if title:
        snippets.append(title)

    if summary:
        snippets.append(summary)

    snippets.append(
        f"Mapped to narrative '{taxonomy_entry['display_name']}' because the article language aligns with factors: "
        f"{', '.join(taxonomy_entry['affected_factors'])}."
    )

    return snippets


def extract_news_narrative(
    title: str,
    summary: str = "",
    provided_tickers: list[str] | None = None,
    top_k: int = 3,
) -> dict:
    taxonomy = load_narrative_taxonomy()

    classification = predict_narrative(
        title=title,
        summary=summary,
        top_k=top_k,
    )

    label = classification["predicted_label"]
    taxonomy_entry = taxonomy.get(label)

    if taxonomy_entry is None:
        taxonomy_entry = {
            "display_name": label,
            "description": "No taxonomy entry found.",
            "affected_factors": [],
            "default_tickers": [],
            "severity_keywords": [],
            "base_severity": 0.50,
        }

    text = f"{title}. {summary}".strip()

    extracted_tickers = extract_tickers_from_text(text)
    tickers = sorted(set((provided_tickers or []) + extracted_tickers + taxonomy_entry["default_tickers"]))

    severity = estimate_narrative_severity(
        text=text,
        base_severity=float(taxonomy_entry["base_severity"]),
        confidence=float(classification["confidence"]),
        severity_keywords=taxonomy_entry["severity_keywords"],
    )

    return {
        "narrative": label,
        "display_name": taxonomy_entry["display_name"],
        "description": taxonomy_entry["description"],
        "severity": severity,
        "confidence": classification["confidence"],
        "affected_tickers": tickers,
        "affected_factors": taxonomy_entry["affected_factors"],
        "evidence": build_evidence_snippets(
            title=title,
            summary=summary,
            label=label,
            taxonomy_entry=taxonomy_entry,
        ),
        "classification": classification,
    }


def extract_batch_news_narratives(articles: list[dict]) -> list[dict]:
    results = []

    for article in articles:
        results.append(
            extract_news_narrative(
                title=article.get("title", ""),
                summary=article.get("summary", ""),
                provided_tickers=article.get("tickers", []),
            )
        )

    return results
