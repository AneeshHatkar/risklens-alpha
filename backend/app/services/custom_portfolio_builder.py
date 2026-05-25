from __future__ import annotations

from backend.app.schemas import Holding, Portfolio


def normalize_custom_holdings(holdings: list[dict]) -> list[Holding]:
    if not holdings:
        raise ValueError("At least one holding is required.")

    cleaned = []

    for item in holdings:
        ticker = str(item.get("ticker", "")).strip().upper()
        weight = item.get("weight")
        shares = item.get("shares")

        if not ticker:
            raise ValueError("Every holding must include a ticker.")

        if weight is None and shares is None:
            raise ValueError(f"Holding {ticker} must include either weight or shares.")

        cleaned.append(
            {
                "ticker": ticker,
                "weight": float(weight) if weight is not None else None,
                "shares": float(shares) if shares is not None else None,
            }
        )

    weighted = [item for item in cleaned if item["weight"] is not None]

    if weighted:
        total_weight = sum(item["weight"] for item in weighted)

        if total_weight <= 0:
            raise ValueError("Portfolio weights must sum to a positive value.")

        return [
            Holding(
                ticker=item["ticker"],
                weight=round(item["weight"] / total_weight, 6),
                shares=item["shares"],
            )
            for item in cleaned
            if item["weight"] is not None
        ]

    # If only shares are supplied and no prices are supplied here, distribute equally.
    equal_weight = round(1.0 / len(cleaned), 6)

    return [
        Holding(
            ticker=item["ticker"],
            weight=equal_weight,
            shares=item["shares"],
        )
        for item in cleaned
    ]


def build_custom_portfolio(
    name: str,
    holdings: list[dict],
) -> Portfolio:
    normalized_holdings = normalize_custom_holdings(holdings)

    return Portfolio(
        name=name or "Custom Portfolio",
        holdings=normalized_holdings,
    )
