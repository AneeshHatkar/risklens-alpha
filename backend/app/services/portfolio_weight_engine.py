from backend.app.schemas import (
    Holding,
    LiveWeightHoldingResult,
    LiveWeightRequest,
    LiveWeightResult,
    Portfolio,
)
from backend.app.services.market_data_loader import get_latest_prices
from backend.app.services.portfolio_parser import normalize_ticker


def recalculate_weights_from_shares(request: LiveWeightRequest) -> LiveWeightResult:
    tickers = [normalize_ticker(holding.ticker) for holding in request.holdings]

    price_result = get_latest_prices(
        tickers=tickers,
        start=request.start,
        use_cache=request.use_cache,
    )

    prices = price_result["prices"]
    warnings = list(price_result["market_data"].get("warnings", []))

    intermediate = []
    total_market_value = 0.0

    for holding in request.holdings:
        ticker = normalize_ticker(holding.ticker)
        price_info = prices.get(ticker, {})
        latest_price = price_info.get("latest_price")
        available = bool(price_info.get("available", False))

        if not available or latest_price is None:
            warning = f"Price unavailable for {ticker}; holding excluded from live-weight total."
            warnings.append(warning)
            intermediate.append(
                LiveWeightHoldingResult(
                    ticker=ticker,
                    shares=holding.shares,
                    latest_price=None,
                    market_value=None,
                    weight=None,
                    cost_basis=holding.cost_basis,
                    available=False,
                    warning=warning,
                )
            )
            continue

        market_value = float(holding.shares) * float(latest_price)
        total_market_value += market_value

        intermediate.append(
            LiveWeightHoldingResult(
                ticker=ticker,
                shares=holding.shares,
                latest_price=round(float(latest_price), 4),
                market_value=round(market_value, 4),
                weight=None,
                cost_basis=holding.cost_basis,
                available=True,
                warning=None,
            )
        )

    final_holdings = []
    normalized_holdings = []

    for item in intermediate:
        if item.available and item.market_value is not None and total_market_value > 0:
            weight = item.market_value / total_market_value
            updated = item.model_copy(update={"weight": round(weight, 6)})
            normalized_holdings.append(
                Holding(
                    ticker=item.ticker,
                    weight=round(weight, 6),
                    shares=item.shares,
                    cost_basis=item.cost_basis,
                )
            )
        else:
            updated = item

        final_holdings.append(updated)

    if total_market_value <= 0:
        warnings.append("Total market value is zero; normalized portfolio could not be created.")

    normalized_portfolio = Portfolio(
        name=request.name,
        holdings=normalized_holdings,
    )

    return LiveWeightResult(
        name=request.name,
        total_market_value=round(total_market_value, 4),
        holdings=final_holdings,
        normalized_portfolio=normalized_portfolio,
        warnings=warnings,
    )
