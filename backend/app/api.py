from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.config import get_settings

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
from backend.app.database import get_db, init_db
from backend.app.schemas import (
    AssetProfile,
    AssetSearchResult,
    PortfolioCreateRequest,
    PortfolioDetail,
    PortfolioSummary,
    ScenarioComparisonRequest,
    SimulationRequest,
    SimulationResult,
    WatchlistCreateRequest,
    WatchlistItem,
    WhatIfRequest,
    HistoricalReplayRequest,
    BenchmarkComparisonRequest,
    AlertCheckRequest,
    LiveWeightRequest,
    NarrativeClassificationRequest,
    NewsNarrativeExtractionRequest,
    DynamicFactorUpdateRequest,
    RiskCalibrationRequest,
    NewsAwareSimulationRequest,
    LiveNewsRequest,
    LiveNewsSimulationRequest,
    CustomLiveNewsSimulationRequest,
)
from backend.app.services.portfolio_repository import (
    create_portfolio,
    delete_portfolio,
    get_portfolio_by_id,
    list_portfolios,
    portfolio_detail,
    portfolio_model_to_schema,
    portfolio_summary,
)
from backend.app.services.simulation_repository import (
    get_simulation_run,
    list_simulation_runs,
    save_simulation_run,
    simulation_run_detail,
    simulation_run_summary,
)
from backend.app.services.watchlist_repository import (
    add_watchlist_item,
    delete_watchlist_item,
    list_watchlist_items,
    watchlist_item_to_dict,
)
from backend.app.services.scenario_generator import SCENARIOS
from backend.app.services.factor_mapper import map_factors
from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.risk_scoring import score_portfolio
from backend.app.services.confidence_engine import calculate_confidence_interval
from backend.app.services.hidden_concentration import calculate_hidden_concentration
from backend.app.services.evidence_tracker import build_simulation_evidence
from backend.app.services.report_generator import render_risk_report_html
from backend.app.services.pdf_report import render_risk_report_pdf
from backend.app.services.evaluation_runner import run_evaluation_suite
from backend.app.services.historical_shocks import list_historical_shocks, replay_historical_shock
from backend.app.services.benchmark_comparison import list_benchmarks, compare_portfolio_to_benchmarks
from backend.app.services.job_manager import get_scheduler_status, run_market_refresh_job, start_scheduler, stop_scheduler
from backend.app.services.timeline_repository import list_timeline_points, save_timeline_point, timeline_point_to_dict
from backend.app.services.alert_engine import check_alerts_for_portfolios
from backend.app.services.alert_repository import alert_to_dict, delete_alert, list_alerts, mark_alert_read
from backend.app.services.job_manager import run_alert_check_job
from backend.app.services.portfolio_weight_engine import recalculate_weights_from_shares
from backend.app.ml.narrative_classifier import load_model_metrics, predict_narrative
from backend.app.services.news_narrative_extractor import extract_batch_news_narratives
from backend.app.services.dynamic_factor_updater import run_dynamic_factor_update
from backend.app.services.agent_disagreement import calculate_agent_disagreement
from backend.app.ml.risk_calibrator import load_risk_calibrator_metrics, predict_calibrated_risk_from_result
from backend.app.services.news_aware_simulation import run_news_aware_simulation
from backend.app.services.ml_evaluation import run_ml_evaluation_suite
from backend.app.ml.risk_anomaly_detector import detect_risk_timeline_anomalies
from backend.app.services.live_news import fetch_live_market_news_safe
from backend.app.services.custom_portfolio_builder import build_custom_portfolio


settings = get_settings()

app = FastAPI(
    title=f"{settings.app_name} API",
    description=(
        "API for portfolio shock simulation, factor exposure analysis, "
        "multi-agent risk debate, and explainable vulnerability scoring."
    ),
    version=settings.app_version,
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

# Create local SQLite tables on startup for the personal/local version.
init_db()


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "risklens-alpha-api",
        "version": "0.1.0",
    }





@app.get("/config/status")
def config_status() -> dict:
    settings = get_settings()
    return settings.public_config()

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
            settings = get_settings()
            market_metrics = compute_market_metrics(
                portfolio=portfolio,
                start=settings.market_data_start_date,
                benchmark=settings.market_data_benchmark,
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



@app.post("/db/portfolios", response_model=PortfolioSummary)
def create_database_portfolio(
    request: PortfolioCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    portfolio = create_portfolio(db, request)
    return portfolio_summary(portfolio)


@app.get("/db/portfolios", response_model=list[PortfolioSummary])
def list_database_portfolios(db: Session = Depends(get_db)) -> list[dict]:
    return [portfolio_summary(item) for item in list_portfolios(db)]


@app.get("/db/portfolios/{portfolio_id}", response_model=PortfolioDetail)
def get_database_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
) -> dict:
    portfolio = get_portfolio_by_id(db, portfolio_id)

    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    return portfolio_detail(portfolio)


@app.delete("/db/portfolios/{portfolio_id}")
def delete_database_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
) -> dict:
    deleted = delete_portfolio(db, portfolio_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    return {"deleted": True, "portfolio_id": portfolio_id}


@app.post("/db/portfolios/{portfolio_id}/simulate")
def simulate_database_portfolio(
    portfolio_id: int,
    request: SimulationRequest,
    db: Session = Depends(get_db),
) -> dict:
    portfolio_model = get_portfolio_by_id(db, portfolio_id)

    if portfolio_model is None:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    portfolio = portfolio_model_to_schema(portfolio_model)
    scenario = get_scenario(request.scenario_id)

    market_metrics = None
    if request.use_market_data:
        settings = get_settings()
        market_metrics = compute_market_metrics(
            portfolio=portfolio,
            start=settings.market_data_start_date,
            benchmark=settings.market_data_benchmark,
        )

    exposures = map_factors(portfolio, scenario)
    agent_opinions = run_agent_debate(portfolio, scenario, exposures)

    score, risk_level, factor_contributions, holding_risks = score_portfolio(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        agent_opinions=agent_opinions,
        market_metrics=market_metrics,
    )

    dominant_factors = list(factor_contributions.keys())
    most_vulnerable_holdings = [
        holding.ticker for holding in holding_risks
        if holding.risk_score >= 20
    ][:3]

    confidence_interval = calculate_confidence_interval(
        score=score,
        portfolio=portfolio,
        exposures=exposures,
        agent_opinions=agent_opinions,
        market_metrics=market_metrics,
    )

    hidden_concentration = calculate_hidden_concentration(
        portfolio=portfolio,
        exposures=exposures,
    )

    evidence_items = build_simulation_evidence(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        holding_risks=holding_risks,
        agent_opinions=agent_opinions,
        hidden_concentration=hidden_concentration,
        market_metrics=market_metrics,
    )

    agent_disagreement = calculate_agent_disagreement(agent_opinions)

    summary = (
        f"The portfolio has a {risk_level} simulated vulnerability score of {score}/100 "
        f"under the '{scenario.name}' scenario. The dominant mapped risk themes are "
        f"{', '.join(dominant_factors[:4])}."
    )

    result = SimulationResult(
        portfolio_name=portfolio.name,
        scenario=scenario,
        vulnerability_score=score,
        risk_level=risk_level,
        dominant_factors=dominant_factors,
        most_vulnerable_holdings=most_vulnerable_holdings,
        holding_risks=holding_risks,
        factor_contributions=factor_contributions,
        agent_opinions=agent_opinions,
        summary=summary,
        disclaimer=(
            "Educational scenario analysis only. This is not financial advice, "
            "does not recommend buying or selling securities, and does not guarantee future returns."
        ),
        market_metrics=market_metrics,
        confidence_interval=confidence_interval,
        hidden_concentration=hidden_concentration,
        evidence_items=evidence_items,
        agent_disagreement=agent_disagreement,
    )

    run = save_simulation_run(
        db=db,
        portfolio_id=portfolio_id,
        scenario_id=request.scenario_id,
        result=result,
    )

    timeline_point = save_timeline_point(
        db=db,
        portfolio_id=portfolio_id,
        scenario_id=request.scenario_id,
        result=result,
        source="database_simulation",
    )

    return {
        "simulation_run_id": run.id,
        "timeline_point_id": timeline_point.id,
        "result": result.model_dump(mode="json"),
    }


@app.get("/db/simulation-runs")
def list_database_simulation_runs(
    portfolio_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    return [
        simulation_run_summary(item)
        for item in list_simulation_runs(db, portfolio_id=portfolio_id)
    ]


@app.get("/db/simulation-runs/{run_id}")
def get_database_simulation_run(
    run_id: int,
    db: Session = Depends(get_db),
) -> dict:
    run = get_simulation_run(db, run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="Simulation run not found.")

    return simulation_run_detail(run)


@app.post("/db/watchlist", response_model=WatchlistItem)
def add_database_watchlist_item(
    request: WatchlistCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    item = add_watchlist_item(
        db=db,
        ticker=request.ticker,
        name=request.name,
        notes=request.notes,
    )

    return watchlist_item_to_dict(item)


@app.get("/db/watchlist", response_model=list[WatchlistItem])
def list_database_watchlist(db: Session = Depends(get_db)) -> list[dict]:
    return [watchlist_item_to_dict(item) for item in list_watchlist_items(db)]


@app.delete("/db/watchlist/{item_id}")
def delete_database_watchlist_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> dict:
    deleted = delete_watchlist_item(db, item_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist item not found.")

    return {"deleted": True, "watchlist_item_id": item_id}



@app.post("/reports/sample")
def generate_sample_report(request: SimulationRequest) -> dict:
    try:
        result = run_simulation(
            portfolio_id=request.portfolio_id,
            scenario_id=request.scenario_id,
            use_market_data=request.use_market_data,
        )

        output_path = render_risk_report_html(
            result=result,
            output_path=f"reports/html/{request.portfolio_id}_{request.scenario_id}_report.html",
        )

        return {
            "report_type": "html",
            "path": str(output_path),
            "portfolio_name": result.portfolio_name,
            "scenario_name": result.scenario.name,
            "vulnerability_score": result.vulnerability_score,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error



@app.post("/reports/sample/pdf")
def generate_sample_pdf_report(request: SimulationRequest) -> dict:
    try:
        result = run_simulation(
            portfolio_id=request.portfolio_id,
            scenario_id=request.scenario_id,
            use_market_data=request.use_market_data,
        )

        output_path = render_risk_report_pdf(
            result=result,
            html_output_path=f"reports/html/{request.portfolio_id}_{request.scenario_id}_report.html",
            pdf_output_path=f"reports/pdf/{request.portfolio_id}_{request.scenario_id}_report.pdf",
        )

        return {
            "report_type": "pdf",
            "path": str(output_path),
            "portfolio_name": result.portfolio_name,
            "scenario_name": result.scenario.name,
            "vulnerability_score": result.vulnerability_score,
        }

    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error



@app.get("/evaluate")
def evaluate_system(use_market_data: bool = False) -> dict:
    return run_evaluation_suite(use_market_data=use_market_data)



@app.get("/historical-shocks")
def get_historical_shocks() -> dict:
    return list_historical_shocks()


@app.post("/historical-replay")
def run_historical_replay(request: HistoricalReplayRequest) -> dict:
    try:
        raw_portfolios = load_all_sample_portfolios()

        if request.portfolio_id not in raw_portfolios:
            valid = ", ".join(raw_portfolios.keys())
            raise ValueError(
                f"Unknown portfolio_id '{request.portfolio_id}'. Valid options: {valid}"
            )

        portfolio = normalize_portfolio(raw_portfolios[request.portfolio_id])

        return replay_historical_shock(
            portfolio=portfolio,
            shock_id=request.shock_id,
            use_cache=request.use_cache,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error



@app.get("/benchmarks")
def get_available_benchmarks() -> dict:
    return list_benchmarks()


@app.post("/benchmarks/compare")
def compare_benchmarks(request: BenchmarkComparisonRequest) -> dict:
    try:
        raw_portfolios = load_all_sample_portfolios()

        if request.portfolio_id not in raw_portfolios:
            valid = ", ".join(raw_portfolios.keys())
            raise ValueError(
                f"Unknown portfolio_id '{request.portfolio_id}'. Valid options: {valid}"
            )

        portfolio = normalize_portfolio(raw_portfolios[request.portfolio_id])

        return compare_portfolio_to_benchmarks(
            portfolio=portfolio,
            benchmark_tickers=request.benchmark_tickers,
            start=request.start,
            end=request.end,
            use_cache=request.use_cache,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error



@app.get("/jobs/status")
def get_jobs_status() -> dict:
    return get_scheduler_status()


@app.post("/jobs/start")
def start_background_jobs() -> dict:
    return start_scheduler()


@app.post("/jobs/stop")
def stop_background_jobs() -> dict:
    return stop_scheduler()


@app.post("/jobs/run-market-refresh")
def run_market_refresh_now() -> dict:
    return run_market_refresh_job()


@app.get("/db/portfolios/{portfolio_id}/timeline")
def get_portfolio_risk_timeline(
    portfolio_id: int,
    scenario_id: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[dict]:
    portfolio = get_portfolio_by_id(db, portfolio_id)

    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    points = list_timeline_points(
        db=db,
        portfolio_id=portfolio_id,
        scenario_id=scenario_id,
        limit=limit,
    )

    return [timeline_point_to_dict(point) for point in points]



@app.post("/alerts/check")
def check_alerts(
    request: AlertCheckRequest,
    db: Session = Depends(get_db),
) -> dict:
    return check_alerts_for_portfolios(
        db=db,
        portfolio_id=request.portfolio_id,
        risk_threshold=request.risk_threshold,
        hidden_concentration_threshold=request.hidden_concentration_threshold,
        volatility_threshold=request.volatility_threshold,
        correlation_threshold=request.correlation_threshold,
    )


@app.get("/alerts")
def get_alerts(
    portfolio_id: int | None = None,
    unread_only: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[dict]:
    return [
        alert_to_dict(alert)
        for alert in list_alerts(
            db=db,
            portfolio_id=portfolio_id,
            unread_only=unread_only,
            limit=limit,
        )
    ]


@app.post("/alerts/{alert_id}/read")
def mark_alert_as_read(
    alert_id: int,
    db: Session = Depends(get_db),
) -> dict:
    alert = mark_alert_read(db, alert_id)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found.")

    return alert_to_dict(alert)


@app.delete("/alerts/{alert_id}")
def delete_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
) -> dict:
    deleted = delete_alert(db, alert_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found.")

    return {"deleted": True, "alert_id": alert_id}


@app.post("/jobs/run-alert-check")
def run_alert_check_now() -> dict:
    return run_alert_check_job()



@app.post("/portfolio/recalculate-weights")
def recalculate_portfolio_weights(request: LiveWeightRequest) -> dict:
    result = recalculate_weights_from_shares(request)
    return result.model_dump(mode="json")



@app.post("/ml/narratives/classify")
def classify_news_narrative(request: NarrativeClassificationRequest) -> dict:
    try:
        return predict_narrative(
            title=request.title,
            summary=request.summary,
            top_k=request.top_k,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/ml/narratives/metrics")
def get_narrative_classifier_metrics() -> dict:
    try:
        return load_model_metrics()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error



@app.post("/news/extract-narratives")
def extract_news_narratives(request: NewsNarrativeExtractionRequest) -> dict:
    articles = [
        article.model_dump(mode="json")
        for article in request.articles
    ]

    try:
        narratives = extract_batch_news_narratives(articles)
        return {
            "count": len(narratives),
            "narratives": narratives,
        }
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error



@app.post("/factors/dynamic-update")
def dynamic_factor_update(request: DynamicFactorUpdateRequest) -> dict:
    articles = [
        article.model_dump(mode="json")
        for article in request.articles
    ]

    try:
        return run_dynamic_factor_update(
            articles=articles,
            tickers=request.tickers,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error



@app.post("/ml/risk-calibrate")
def calibrate_risk_with_ml(request: RiskCalibrationRequest) -> dict:
    try:
        result = run_simulation(
            portfolio_id=request.portfolio_id,
            scenario_id=request.scenario_id,
            use_market_data=request.use_market_data,
        )

        return predict_calibrated_risk_from_result(result)

    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/ml/risk-calibrator/metrics")
def get_risk_calibrator_metrics() -> dict:
    try:
        return load_risk_calibrator_metrics()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error



@app.post("/simulate-with-news")
def simulate_with_news(request: NewsAwareSimulationRequest) -> dict:
    try:
        raw_portfolios = load_all_sample_portfolios()

        if request.portfolio_id not in raw_portfolios:
            valid = ", ".join(raw_portfolios.keys())
            raise ValueError(
                f"Unknown portfolio_id '{request.portfolio_id}'. Valid options: {valid}"
            )

        portfolio = normalize_portfolio(raw_portfolios[request.portfolio_id])
        scenario = get_scenario(request.scenario_id)

        articles = [
            article.model_dump(mode="json")
            for article in request.articles
        ]

        return run_news_aware_simulation(
            portfolio=portfolio,
            scenario=scenario,
            articles=articles,
            use_market_data=request.use_market_data,
            run_ml_calibration=request.run_ml_calibration,
        )

    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error



@app.get("/ml/evaluate")
def evaluate_ml_system() -> dict:
    return run_ml_evaluation_suite()



@app.get("/db/portfolios/{portfolio_id}/timeline/anomalies")
def get_portfolio_timeline_anomalies(
    portfolio_id: int,
    scenario_id: str | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
) -> dict:
    portfolio = get_portfolio_by_id(db, portfolio_id)

    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    points = list_timeline_points(
        db=db,
        portfolio_id=portfolio_id,
        scenario_id=scenario_id,
        limit=limit,
    )

    point_dicts = [timeline_point_to_dict(point) for point in points]

    return detect_risk_timeline_anomalies(point_dicts)



@app.post("/news/live")
def fetch_live_news(request: LiveNewsRequest) -> dict:
    return fetch_live_market_news_safe(
        tickers=request.tickers,
        query=request.query,
        max_articles=request.max_articles,
    )


@app.post("/simulate-with-live-news")
def simulate_with_live_news(request: LiveNewsSimulationRequest) -> dict:
    try:
        raw_portfolios = load_all_sample_portfolios()

        if request.portfolio_id not in raw_portfolios:
            valid = ", ".join(raw_portfolios.keys())
            raise ValueError(
                f"Unknown portfolio_id '{request.portfolio_id}'. Valid options: {valid}"
            )

        portfolio = normalize_portfolio(raw_portfolios[request.portfolio_id])
        scenario = get_scenario(request.scenario_id)

        request_tickers = request.tickers or [holding.ticker for holding in portfolio.holdings]

        live_news = fetch_live_market_news_safe(
            tickers=request_tickers,
            query=request.query,
            max_articles=request.max_articles,
        )

        output = run_news_aware_simulation(
            portfolio=portfolio,
            scenario=scenario,
            articles=live_news["articles"],
            use_market_data=request.use_market_data,
            run_ml_calibration=request.run_ml_calibration,
        )

        output["live_news"] = live_news
        output["live_market_data_enabled"] = request.use_market_data

        return output

    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error



@app.post("/simulate-custom-live-news")
def simulate_custom_portfolio_with_live_news(request: CustomLiveNewsSimulationRequest) -> dict:
    try:
        portfolio = build_custom_portfolio(
            name=request.portfolio_name,
            holdings=[
                holding.model_dump(mode="json")
                for holding in request.holdings
            ],
        )

        scenario = get_scenario(request.scenario_id)

        portfolio_tickers = [holding.ticker for holding in portfolio.holdings]
        request_tickers = request.news_tickers or portfolio_tickers

        live_news = fetch_live_market_news_safe(
            tickers=request_tickers,
            query=request.query,
            max_articles=request.max_articles,
        )

        output = run_news_aware_simulation(
            portfolio=portfolio,
            scenario=scenario,
            articles=live_news["articles"],
            use_market_data=request.use_market_data,
            run_ml_calibration=request.run_ml_calibration,
        )

        output["live_news"] = live_news
        output["custom_portfolio"] = True
        output["live_market_data_enabled"] = request.use_market_data

        return output

    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
