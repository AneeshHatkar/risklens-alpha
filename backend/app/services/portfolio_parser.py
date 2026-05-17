from backend.app.schemas import Portfolio, Holding


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def normalize_portfolio(raw_portfolio: dict) -> Portfolio:
    raw_holdings = []

    for item in raw_portfolio["holdings"]:
        ticker = normalize_ticker(item["ticker"])
        weight = float(item["weight"])

        if weight < 0:
            raise ValueError(f"Weight for {ticker} cannot be negative.")

        raw_holdings.append(
            {
                "ticker": ticker,
                "weight": weight,
                "shares": item.get("shares"),
                "cost_basis": item.get("cost_basis"),
            }
        )

    total_weight = sum(item["weight"] for item in raw_holdings)

    if total_weight <= 0:
        raise ValueError("Portfolio total weight must be greater than 0.")

    # Supports both decimal weights such as 0.35 and percentage-like weights such as 35.
    normalized_items = []
    for item in raw_holdings:
        normalized_items.append(
            {
                **item,
                "weight": item["weight"] / total_weight,
            }
        )

    seen = set()
    duplicates = []

    for item in normalized_items:
        if item["ticker"] in seen:
            duplicates.append(item["ticker"])
        seen.add(item["ticker"])

    if duplicates:
        raise ValueError(f"Duplicate tickers found: {duplicates}")

    holdings = [
        Holding(
            ticker=item["ticker"],
            weight=item["weight"],
            shares=item["shares"],
            cost_basis=item["cost_basis"],
        )
        for item in normalized_items
    ]

    return Portfolio(name=raw_portfolio["name"], holdings=holdings)
