from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.main import (
    load_all_sample_portfolios,
    run_simulation,
    save_result_json,
)
from backend.app.services.market_metrics import compute_market_metrics
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.scenario_comparison import compare_scenarios
from backend.app.services.what_if import compare_what_if_portfolios
from backend.app.services.scenario_generator import get_scenario
from backend.app.services.asset_explorer import find_assets, get_asset_profile
from backend.app.schemas import AssetProfile, AssetSearchResult, ScenarioComparisonRequest, SimulationRequest, SimulationResult, WhatIfRequest
from backend.app.services.scenario_generator import SCENARIOS


app = FastAPI(
    title="RiskLens Alpha API",
    description=(
        "API for portfolio shock simulation, factor exposure analysis, "
        "multi-agent risk debate, and explainable vulnerability scoring."
    ),
    version="0.1.0",
)

# This is intentionally open during local development.
# Later, we can restrict it when the frontend domain is finalized.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "risklens-alpha-api",
        "version": "0.1.0",
    }


@app.get("/portfolios/samples")
def get_sample_portfolios() -> dict:
    return load_all_sample_portfolios()


@app.get("/scenarios")
def get_scenarios() -> dict:
    return {
        scenario_id: scenario.model_dump(mode="json")
        for scenario_id, scenario in SCENARIOS.items()
    }


@app.post("/simulate", response_model=SimulationResult)
def simulate(request: SimulationRequest) -> SimulationResult:
    try:
        result = run_simulation(
            portfolio_id=request.portfolio_id,
            scenario_id=request.scenario_id,
            use_market_data=request.use_market_data,
        )

        if request.save_json:
            output_path = (
                f"reports/json/{request.portfolio_id}_{request.scenario_id}_api_result.json"
            )
            save_result_json(result, output_path)

        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/simulate/compare")
def compare_simulation_scenarios(request: ScenarioComparisonRequest) -> list[dict]:
    try:
        raw_portfolios = load_all_sample_portfolios()

        if request.portfolio_id not in raw_portfolios:
            valid = ", ".join(raw_portfolios.keys())
            raise ValueError(
                f"Unknown portfolio_id '{request.portfolio_id}'. Valid options: {valid}"
            )

        portfolio = normalize_portfolio(raw_portfolios[request.portfolio_id])

        market_metrics = None
        if request.use_market_data:
            market_metrics = compute_market_metrics(
                portfolio=portfolio,
                start="2024-01-01",
                benchmark="SPY",
            )

        return compare_scenarios(
            portfolio=portfolio,
            market_metrics=market_metrics,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/simulate/what-if")
def simulate_what_if(request: WhatIfRequest) -> dict:
    try:
        raw_portfolios = load_all_sample_portfolios()

        if request.base_portfolio_id not in raw_portfolios:
            valid = ", ".join(raw_portfolios.keys())
            raise ValueError(
                f"Unknown portfolio_id '{request.base_portfolio_id}'. Valid options: {valid}"
            )

        base_portfolio = normalize_portfolio(raw_portfolios[request.base_portfolio_id])

        what_if_raw = {
            "name": f"What-if version of {base_portfolio.name}",
            "holdings": [
                holding.model_dump(mode="json")
                for holding in request.what_if_holdings
            ],
        }
        what_if_portfolio = normalize_portfolio(what_if_raw)

        scenario = get_scenario(request.scenario_id)

        market_metrics = None
        if request.use_market_data:
            market_metrics = compute_market_metrics(
                portfolio=base_portfolio,
                start="2024-01-01",
                benchmark="SPY",
            )

        return compare_what_if_portfolios(
            base_portfolio=base_portfolio,
            what_if_portfolio=what_if_portfolio,
            scenario=scenario,
            market_metrics=market_metrics,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/assets/search", response_model=list[AssetSearchResult])
def search_asset_universe(query: str, limit: int = 10) -> list[AssetSearchResult]:
    return find_assets(query=query, limit=limit)


@app.get("/assets/{ticker}", response_model=AssetProfile)
def get_asset_detail(ticker: str, use_market_data: bool = True) -> AssetProfile:
    return get_asset_profile(
        ticker=ticker,
        use_market_data=use_market_data,
    )
