from __future__ import annotations

from backend.app.services.factor_mapper import TICKER_FACTOR_MAP
from backend.app.services.news_narrative_extractor import extract_batch_news_narratives
from backend.app.services.portfolio_parser import normalize_ticker


def get_base_factor_exposure(ticker: str, factor: str) -> dict:
    clean_ticker = normalize_ticker(ticker)
    factor_map = TICKER_FACTOR_MAP.get(clean_ticker, {})

    if factor not in factor_map:
        return {
            "ticker": clean_ticker,
            "factor": factor,
            "base_score": 0.0,
            "base_confidence": 0.0,
            "base_evidence": [],
            "exists_in_base_map": False,
        }

    score, confidence, evidence = factor_map[factor]

    return {
        "ticker": clean_ticker,
        "factor": factor,
        "base_score": float(score),
        "base_confidence": float(confidence),
        "base_evidence": evidence,
        "exists_in_base_map": True,
    }


def calculate_factor_adjustment(
    ticker: str,
    factor: str,
    narrative: dict,
) -> dict:
    affected_tickers = set(narrative.get("affected_tickers", []))
    affected_factors = set(narrative.get("affected_factors", []))

    ticker_match = ticker in affected_tickers
    factor_match = factor in affected_factors

    if not ticker_match and not factor_match:
        return {
            "adjustment": 0.0,
            "reason": "No ticker or factor match.",
            "ticker_match": False,
            "factor_match": False,
        }

    severity = float(narrative.get("severity", 0.0))
    confidence = float(narrative.get("confidence", 0.0))

    # ML classifier confidence is still low because dataset is small.
    # Use severity as the main driver and confidence as a modest multiplier.
    confidence_boost = 0.65 + min(0.35, confidence)

    if ticker_match and factor_match:
        raw_adjustment = 0.18 * severity * confidence_boost
        reason = "Ticker and factor both matched narrative."
    elif factor_match:
        raw_adjustment = 0.10 * severity * confidence_boost
        reason = "Factor matched narrative."
    else:
        raw_adjustment = 0.06 * severity * confidence_boost
        reason = "Ticker matched narrative."

    return {
        "adjustment": round(min(0.20, raw_adjustment), 4),
        "reason": reason,
        "ticker_match": ticker_match,
        "factor_match": factor_match,
    }


def update_factor_exposure_for_ticker(
    ticker: str,
    factors: list[str],
    narratives: list[dict],
) -> list[dict]:
    clean_ticker = normalize_ticker(ticker)
    updates = []

    for factor in factors:
        base = get_base_factor_exposure(clean_ticker, factor)

        total_adjustment = 0.0
        narrative_evidence = []

        for narrative in narratives:
            adjustment_result = calculate_factor_adjustment(
                ticker=clean_ticker,
                factor=factor,
                narrative=narrative,
            )

            adjustment = adjustment_result["adjustment"]
            if adjustment <= 0:
                continue

            total_adjustment += adjustment
            narrative_evidence.append(
                {
                    "narrative": narrative.get("narrative"),
                    "display_name": narrative.get("display_name"),
                    "severity": narrative.get("severity"),
                    "confidence": narrative.get("confidence"),
                    "adjustment": adjustment,
                    "reason": adjustment_result["reason"],
                    "evidence": narrative.get("evidence", []),
                }
            )

        # Cap total narrative impact.
        total_adjustment = min(0.25, total_adjustment)

        dynamic_score = min(1.0, base["base_score"] + total_adjustment)

        # If factor did not exist in base map but narrative strongly supports it,
        # create a small dynamic exposure.
        if not base["exists_in_base_map"] and total_adjustment > 0:
            dynamic_score = max(dynamic_score, min(0.45, total_adjustment * 2.0))

        dynamic_confidence = min(
            1.0,
            max(base["base_confidence"], 0.55 if total_adjustment > 0 else base["base_confidence"])
            + min(0.15, total_adjustment),
        )

        updates.append(
            {
                "ticker": clean_ticker,
                "factor": factor,
                "base_score": round(base["base_score"], 4),
                "dynamic_score": round(dynamic_score, 4),
                "adjustment": round(total_adjustment, 4),
                "base_confidence": round(base["base_confidence"], 4),
                "dynamic_confidence": round(dynamic_confidence, 4),
                "exists_in_base_map": base["exists_in_base_map"],
                "base_evidence": base["base_evidence"],
                "narrative_evidence": narrative_evidence,
            }
        )

    return sorted(updates, key=lambda item: item["dynamic_score"], reverse=True)


def collect_candidate_factors(tickers: list[str], narratives: list[dict]) -> list[str]:
    factors = set()

    for ticker in tickers:
        factor_map = TICKER_FACTOR_MAP.get(normalize_ticker(ticker), {})
        factors.update(factor_map.keys())

    for narrative in narratives:
        factors.update(narrative.get("affected_factors", []))

    return sorted(factors)


def run_dynamic_factor_update(
    articles: list[dict],
    tickers: list[str],
) -> dict:
    clean_tickers = [normalize_ticker(ticker) for ticker in tickers]
    narratives = extract_batch_news_narratives(articles)

    candidate_factors = collect_candidate_factors(clean_tickers, narratives)

    ticker_updates = {
        ticker: update_factor_exposure_for_ticker(
            ticker=ticker,
            factors=candidate_factors,
            narratives=narratives,
        )
        for ticker in clean_tickers
    }

    return {
        "tickers": clean_tickers,
        "narrative_count": len(narratives),
        "narratives": narratives,
        "candidate_factors": candidate_factors,
        "ticker_updates": ticker_updates,
        "summary": build_dynamic_factor_update_summary(ticker_updates),
        "disclaimer": (
            "Dynamic factor updates are experimental AI/ML-assisted risk signals. "
            "They are not financial advice and should be interpreted as scenario evidence, not predictions."
        ),
    }


def build_dynamic_factor_update_summary(ticker_updates: dict) -> str:
    changed = []

    for ticker, updates in ticker_updates.items():
        for update in updates:
            if update["adjustment"] > 0:
                changed.append(
                    f"{ticker} {update['factor']} adjusted by +{update['adjustment']:.2f} "
                    f"to {update['dynamic_score']:.2f}"
                )

    if not changed:
        return "No dynamic factor adjustments were generated from the supplied news narratives."

    preview = "; ".join(changed[:6])

    if len(changed) > 6:
        preview += f"; and {len(changed) - 6} more adjustments."

    return preview
