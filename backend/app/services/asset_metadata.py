from backend.app.schemas import AssetSearchResult


ASSET_METADATA = {
    "NVDA": {
        "name": "NVIDIA Corporation",
        "asset_type": "equity",
        "sector": "Technology",
        "industry": "Semiconductors",
        "description": "NVIDIA designs GPUs, AI accelerators, and data center computing platforms.",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "asset_type": "equity",
        "sector": "Technology",
        "industry": "Software / Cloud Infrastructure",
        "description": "Microsoft provides cloud, productivity, enterprise software, gaming, and AI platform services.",
    },
    "AAPL": {
        "name": "Apple Inc.",
        "asset_type": "equity",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "description": "Apple designs consumer hardware, software, services, and ecosystem products.",
    },
    "SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "asset_type": "ETF",
        "sector": "Broad Market",
        "industry": "Large-Cap U.S. Equity ETF",
        "description": "SPY tracks the S&P 500 Index and represents broad U.S. large-cap equity exposure.",
    },
    "QQQ": {
        "name": "Invesco QQQ Trust",
        "asset_type": "ETF",
        "sector": "Technology / Growth",
        "industry": "NASDAQ-100 ETF",
        "description": "QQQ tracks the NASDAQ-100 Index and has high exposure to mega-cap technology and growth companies.",
    },
    "SMH": {
        "name": "VanEck Semiconductor ETF",
        "asset_type": "ETF",
        "sector": "Technology",
        "industry": "Semiconductor ETF",
        "description": "SMH tracks semiconductor companies and provides concentrated chip-sector exposure.",
    },
    "AMD": {
        "name": "Advanced Micro Devices, Inc.",
        "asset_type": "equity",
        "sector": "Technology",
        "industry": "Semiconductors",
        "description": "AMD designs CPUs, GPUs, data center processors, and AI accelerator products.",
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "asset_type": "equity",
        "sector": "Communication Services",
        "industry": "Internet Content / Cloud / Advertising",
        "description": "Alphabet operates Google Search, YouTube, Google Cloud, advertising platforms, and AI products.",
    },
    "AMZN": {
        "name": "Amazon.com, Inc.",
        "asset_type": "equity",
        "sector": "Consumer Discretionary",
        "industry": "E-commerce / Cloud Infrastructure",
        "description": "Amazon operates e-commerce, logistics, advertising, subscriptions, and AWS cloud infrastructure.",
    },
    "TSLA": {
        "name": "Tesla, Inc.",
        "asset_type": "equity",
        "sector": "Consumer Discretionary",
        "industry": "Electric Vehicles",
        "description": "Tesla designs electric vehicles, energy storage products, charging infrastructure, and autonomy software.",
    },
}


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def get_asset_metadata(ticker: str) -> dict | None:
    return ASSET_METADATA.get(normalize_ticker(ticker))


def search_assets(query: str, limit: int = 10) -> list[AssetSearchResult]:
    clean_query = query.strip().upper()

    if not clean_query:
        return []

    results = []

    for ticker, metadata in ASSET_METADATA.items():
        name = metadata["name"]
        searchable = f"{ticker} {name} {metadata.get('sector', '')} {metadata.get('industry', '')}".upper()

        if clean_query in searchable:
            results.append(
                AssetSearchResult(
                    ticker=ticker,
                    name=name,
                    asset_type=metadata.get("asset_type", "equity"),
                    sector=metadata.get("sector"),
                    industry=metadata.get("industry"),
                )
            )

    return results[:limit]
