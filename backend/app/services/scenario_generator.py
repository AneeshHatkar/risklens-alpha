from backend.app.schemas import ShockScenario


SCENARIOS = {
    "ai_capex_slowdown": ShockScenario(
        name="AI Infrastructure Spending Slowdown",
        description="Simulates a reset in expectations for AI infrastructure, data center capex, GPU demand, and cloud AI monetization.",
        severity=0.75,
        affected_factors=[
            "AI infrastructure",
            "semiconductors",
            "cloud growth",
            "big-tech correlation",
            "valuation multiples",
        ],
    ),
    "higher_for_longer_rates": ShockScenario(
        name="Higher-for-Longer Interest Rates",
        description="Simulates persistent inflation and elevated interest rates pressuring growth valuations and rate-sensitive assets.",
        severity=0.70,
        affected_factors=[
            "interest rates",
            "valuation multiples",
            "growth stocks",
            "market beta",
            "liquidity conditions",
        ],
    ),
    "cloud_growth_deceleration": ShockScenario(
        name="Cloud Growth Deceleration",
        description="Simulates slower enterprise cloud spending and weaker cloud platform growth expectations.",
        severity=0.65,
        affected_factors=[
            "cloud growth",
            "enterprise IT spend",
            "AI software monetization",
            "valuation multiples",
        ],
    ),
    "semiconductor_export_restriction": ShockScenario(
        name="Semiconductor Export Restriction",
        description="Simulates geopolitical restrictions affecting semiconductor sales, supply chains, and China exposure.",
        severity=0.80,
        affected_factors=[
            "semiconductors",
            "China exposure",
            "hardware supply chain",
            "geopolitical risk",
        ],
    ),
    "consumer_demand_weakness": ShockScenario(
        name="Consumer Demand Weakness",
        description="Simulates weakening consumer spending and pressure on hardware, retail, and discretionary businesses.",
        severity=0.60,
        affected_factors=[
            "consumer demand",
            "hardware cycle",
            "discretionary spending",
            "market beta",
        ],
    ),
}


def get_scenario(scenario_id: str) -> ShockScenario:
    if scenario_id not in SCENARIOS:
        valid = ", ".join(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario_id '{scenario_id}'. Valid options: {valid}")
    return SCENARIOS[scenario_id]


def list_scenarios():
    return list(SCENARIOS.values())
