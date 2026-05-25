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
            "long-duration assets",
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
            "AI infrastructure",
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
            "earnings growth",
        ],
    ),
    "regional_banking_stress": ShockScenario(
        name="Regional Banking Stress",
        description="Simulates renewed stress in regional banks, deposit outflows, credit tightening, and funding pressure.",
        severity=0.70,
        affected_factors=[
            "banking stress",
            "credit risk",
            "deposit flight",
            "interest rates",
            "market beta",
        ],
    ),
    "oil_inflation_shock": ShockScenario(
        name="Oil Inflation Shock",
        description="Simulates an oil-price spike that raises inflation expectations, pressures consumers, and increases rate-sensitive risk.",
        severity=0.68,
        affected_factors=[
            "oil prices",
            "inflation",
            "consumer demand",
            "interest rates",
            "transportation costs",
            "commodity pressure",
        ],
    ),
    "recession_earnings_reset": ShockScenario(
        name="Recession Earnings Reset",
        description="Simulates broad earnings revisions from recession fears, weaker demand, credit tightening, and lower enterprise spending.",
        severity=0.72,
        affected_factors=[
            "earnings growth",
            "consumer demand",
            "enterprise IT spend",
            "market beta",
            "credit risk",
        ],
    ),
    "big_tech_antitrust_shock": ShockScenario(
        name="Big-Tech Antitrust Shock",
        description="Simulates regulatory pressure on large technology platforms, including antitrust actions, platform restrictions, and valuation compression.",
        severity=0.62,
        affected_factors=[
            "big-tech regulation",
            "valuation multiples",
            "platform risk",
            "cloud growth",
            "advertising revenue",
            "big-tech correlation",
        ],
    ),
    "china_taiwan_geopolitical_shock": ShockScenario(
        name="China/Taiwan Geopolitical Shock",
        description="Simulates escalation in China/Taiwan geopolitical risk, semiconductor supply disruption, and global hardware-chain stress.",
        severity=0.82,
        affected_factors=[
            "China exposure",
            "semiconductors",
            "hardware supply chain",
            "geopolitical risk",
            "market beta",
        ],
    ),
    "ai_monetization_disappointment": ShockScenario(
        name="AI Monetization Disappointment",
        description="Simulates investor disappointment around enterprise AI monetization, cloud AI revenue conversion, and software productivity gains.",
        severity=0.66,
        affected_factors=[
            "AI software monetization",
            "AI infrastructure",
            "cloud growth",
            "valuation multiples",
            "enterprise IT spend",
        ],
    ),
    "credit_spread_widening": ShockScenario(
        name="Credit Spread Widening",
        description="Simulates widening credit spreads, tightening financial conditions, and greater default-risk concerns.",
        severity=0.70,
        affected_factors=[
            "credit risk",
            "market beta",
            "interest rates",
            "banking stress",
            "earnings growth",
        ],
    ),
    "dollar_strength_shock": ShockScenario(
        name="Dollar Strength Shock",
        description="Simulates a strong U.S. dollar pressuring multinational revenue, emerging markets, commodities, and global risk assets.",
        severity=0.58,
        affected_factors=[
            "dollar strength",
            "international revenue",
            "emerging markets",
            "commodity pressure",
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
