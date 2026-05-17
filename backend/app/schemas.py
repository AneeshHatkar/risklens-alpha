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


class SimulationRequest(BaseModel):
    portfolio_id: str = "ai_growth_sample"
    scenario_id: str = "ai_capex_slowdown"
    save_json: bool = False
    use_market_data: bool = False
