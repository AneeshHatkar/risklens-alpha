from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.main import (
    load_all_sample_portfolios,
    run_simulation,
    save_result_json,
)
from backend.app.schemas import SimulationRequest, SimulationResult
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
        )

        if request.save_json:
            output_path = (
                f"reports/json/{request.portfolio_id}_{request.scenario_id}_api_result.json"
            )
            save_result_json(result, output_path)

        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
