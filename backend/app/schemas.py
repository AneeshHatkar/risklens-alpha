from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class Holding(BaseModel):
    ticker: str
    weight: float = Field(..., ge=0, le=1)
    shares: Optional[float] = None
    cost_basis: Optional[float] = None


class Portfolio(BaseModel):
    name: str
    holdings: List[Holding]


class ShockScenario(BaseModel):
    name: str
    description: str
    severity: float = Field(..., ge=0, le=1)
    affected_factors: List[str]


class FactorExposure(BaseModel):
    ticker: str
    factor: str
    score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    evidence: List[str]


class HoldingRisk(BaseModel):
    ticker: str
    risk_score: int
    risk_level: str
    reasons: List[str]


class AgentOpinion(BaseModel):
    agent_name: str
    thesis: str
    affected_holdings: List[str]
    confidence: float = Field(..., ge=0, le=1)
    evidence: List[str]
    risks: List[str]
    uncertainty: Optional[str] = None





class EvidenceItem(BaseModel):
    evidence_type: str
    claim: str
    source: str
    ticker: Optional[str] = None
    factor: Optional[str] = None
    value: Optional[float | int | str] = None
    confidence: Optional[float] = None
    details: Dict = {}


class SimulationResult(BaseModel):
    portfolio_name: str
    scenario: ShockScenario
    vulnerability_score: int
    risk_level: str
    dominant_factors: List[str]
    most_vulnerable_holdings: List[str]
    holding_risks: List[HoldingRisk]
    factor_contributions: Dict[str, float]
    agent_opinions: List[AgentOpinion]
    summary: str
    disclaimer: str
    market_metrics: Optional[Dict] = None
    confidence_interval: Optional[Dict] = None
    hidden_concentration: Optional[Dict] = None
    evidence_items: List[EvidenceItem] = []


class SimulationRequest(BaseModel):
    portfolio_id: str = "ai_growth_sample"
    scenario_id: str = "ai_capex_slowdown"
    save_json: bool = False
    use_market_data: bool = False



class ScenarioComparisonRequest(BaseModel):
    portfolio_id: str = "ai_growth_sample"
    use_market_data: bool = False



class WhatIfRequest(BaseModel):
    base_portfolio_id: str = "ai_growth_sample"
    scenario_id: str = "ai_capex_slowdown"
    what_if_holdings: List[Holding]
    use_market_data: bool = False



class AssetSearchResult(BaseModel):
    ticker: str
    name: str
    asset_type: str = "equity"
    sector: Optional[str] = None
    industry: Optional[str] = None


class AssetProfile(BaseModel):
    ticker: str
    name: str
    asset_type: str = "equity"
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    latest_price: Optional[float] = None
    currency: Optional[str] = None
    market_metrics: Optional[Dict] = None
    factor_exposures: List[FactorExposure] = []
    related_scenarios: List[str] = []
    warnings: List[str] = []


class PortfolioCreateRequest(BaseModel):
    name: str
    owner_label: str = "local"
    holdings: List[Holding]


class PortfolioSummary(BaseModel):
    id: int
    name: str
    owner_label: str
    holding_count: int
    created_at: str


class PortfolioDetail(BaseModel):
    id: int
    name: str
    owner_label: str
    holdings: List[Holding]
    created_at: str


class WatchlistCreateRequest(BaseModel):
    ticker: str
    name: Optional[str] = None
    notes: Optional[str] = None


class WatchlistItem(BaseModel):
    id: int
    ticker: str
    name: Optional[str] = None
    notes: Optional[str] = None
    created_at: str


class SimulationRunSummary(BaseModel):
    id: int
    portfolio_id: int
    scenario_id: str
    scenario_name: str
    vulnerability_score: int
    risk_level: str
    created_at: str



class HistoricalReplayRequest(BaseModel):
    portfolio_id: str = "ai_growth_sample"
    shock_id: str = "covid_crash_2020"
    use_cache: bool = True



class BenchmarkComparisonRequest(BaseModel):
    portfolio_id: str = "ai_growth_sample"
    benchmark_tickers: List[str] = ["SPY", "QQQ", "SMH", "XLK"]
    start: str = "2024-01-01"
    end: Optional[str] = None
    use_cache: bool = True


class RiskTimelinePoint(BaseModel):
    id: int
    portfolio_id: int
    scenario_id: str
    scenario_name: str
    vulnerability_score: int
    risk_level: str
    hidden_concentration_score: Optional[int] = None
    confidence_lower: Optional[int] = None
    confidence_upper: Optional[int] = None
    source: str
    created_at: str


class JobRunResult(BaseModel):
    job_name: str
    status: str
    message: str
    details: Dict = {}


class AlertItem(BaseModel):
    id: int
    portfolio_id: int
    alert_type: str
    severity: str
    title: str
    message: str
    scenario_id: Optional[str] = None
    ticker: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    is_read: bool
    created_at: str


class AlertCheckRequest(BaseModel):
    portfolio_id: Optional[int] = None
    risk_threshold: int = 75
    hidden_concentration_threshold: int = 80
    volatility_threshold: float = 0.35
    correlation_threshold: float = 0.70



class LiveWeightHoldingInput(BaseModel):
    ticker: str
    shares: float
    cost_basis: Optional[float] = None


class LiveWeightRequest(BaseModel):
    name: str = "Live Weight Portfolio"
    holdings: List[LiveWeightHoldingInput]
    start: str = "2024-01-01"
    use_cache: bool = True


class LiveWeightHoldingResult(BaseModel):
    ticker: str
    shares: float
    latest_price: Optional[float] = None
    market_value: Optional[float] = None
    weight: Optional[float] = None
    cost_basis: Optional[float] = None
    available: bool = True
    warning: Optional[str] = None


class LiveWeightResult(BaseModel):
    name: str
    total_market_value: float
    holdings: List[LiveWeightHoldingResult]
    normalized_portfolio: Portfolio
    warnings: List[str] = []



class NarrativeClassificationRequest(BaseModel):
    title: str
    summary: str = ""
    top_k: int = 3


class NarrativeClassificationResult(BaseModel):
    title: str
    summary: str
    predicted_label: str
    confidence: float
    top_labels: List[Dict]
    model_path: str
