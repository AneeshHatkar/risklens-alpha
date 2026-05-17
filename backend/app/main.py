import argparse
import json
from pathlib import Path

from backend.app.schemas import SimulationResult
from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.factor_mapper import map_factors
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.risk_scoring import score_portfolio
from backend.app.services.scenario_generator import SCENARIOS, get_scenario


DISCLAIMER = (
    "Educational scenario analysis only. This is not financial advice, "
    "does not recommend buying or selling securities, and does not guarantee future returns."
)


def load_all_sample_portfolios() -> dict:
    data_path = Path(__file__).parent / "data" / "sample_portfolios.json"

    with open(data_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_sample_portfolio(portfolio_id: str) -> dict:
    portfolios = load_all_sample_portfolios()

    if portfolio_id not in portfolios:
        valid = ", ".join(portfolios.keys())
        raise ValueError(f"Unknown portfolio_id '{portfolio_id}'. Valid options: {valid}")

    return portfolios[portfolio_id]


def build_summary(
    score: int,
    risk_level: str,
    dominant_factors: list[str],
    vulnerable_holdings: list[str],
    scenario_name: str,
) -> str:
    factors = ", ".join(dominant_factors[:4]) if dominant_factors else "limited mapped factors"
    holdings = ", ".join(vulnerable_holdings[:3]) if vulnerable_holdings else "no major holding"

    return (
        f"The portfolio has a {risk_level} simulated vulnerability score of {score}/100 "
        f"under the '{scenario_name}' scenario. The dominant mapped risk themes are {factors}. "
        f"The most affected holdings are {holdings}. This result is based on portfolio weights, "
        f"scenario-factor alignment, factor exposure scores, concentration, volatility proxies, "
        f"and structured agent consensus."
    )


def run_simulation(
    portfolio_id: str = "ai_growth_sample",
    scenario_id: str = "ai_capex_slowdown",
) -> SimulationResult:
    raw_portfolio = load_sample_portfolio(portfolio_id)
    portfolio = normalize_portfolio(raw_portfolio)
    scenario = get_scenario(scenario_id)

    exposures = map_factors(portfolio, scenario)
    agent_opinions = run_agent_debate(portfolio, scenario, exposures)

    score, risk_level, factor_contributions, holding_risks = score_portfolio(
        portfolio=portfolio,
        scenario=scenario,
        exposures=exposures,
        agent_opinions=agent_opinions,
    )

    dominant_factors = list(factor_contributions.keys())

    most_vulnerable_holdings = [
        holding.ticker for holding in holding_risks
        if holding.risk_score >= 20
    ][:3]

    summary = build_summary(
        score=score,
        risk_level=risk_level,
        dominant_factors=dominant_factors,
        vulnerable_holdings=most_vulnerable_holdings,
        scenario_name=scenario.name,
    )

    return SimulationResult(
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
        disclaimer=DISCLAIMER,
    )


def save_result_json(result: SimulationResult, output_path: str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = result.model_dump(mode="json")

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    return path


def print_result(result: SimulationResult) -> None:
    print("\n" + "=" * 72)
    print("RiskLens Alpha Simulation Result")
    print("=" * 72)

    print(f"\nPortfolio: {result.portfolio_name}")
    print(f"Scenario : {result.scenario.name}")
    print(f"Severity : {result.scenario.severity:.2f}")

    print("\n--- Portfolio Vulnerability ---")
    print(f"Score     : {result.vulnerability_score}/100")
    print(f"Risk Level: {result.risk_level.upper()}")

    print("\n--- Dominant Risk Factors ---")
    for factor, contribution in result.factor_contributions.items():
        print(f"- {factor}: {contribution:.2f}% contribution")

    print("\n--- Most Vulnerable Holdings ---")
    for holding in result.holding_risks:
        print(f"- {holding.ticker}: {holding.risk_score}/100 ({holding.risk_level})")
        for reason in holding.reasons:
            print(f"  • {reason}")

    print("\n--- Agent Debate ---")
    for agent in result.agent_opinions:
        print(f"\n[{agent.agent_name}] confidence={agent.confidence:.2f}")
        print(agent.thesis)
        if agent.affected_holdings:
            print("Affected holdings:", ", ".join(agent.affected_holdings))
        print("Key risks:", ", ".join(agent.risks))

    print("\n--- Summary ---")
    print(result.summary)

    print("\n--- Disclaimer ---")
    print(result.disclaimer)
    print("=" * 72 + "\n")


def print_available_options() -> None:
    portfolios = load_all_sample_portfolios()

    print("\nAvailable portfolios:")
    for portfolio_id, portfolio in portfolios.items():
        print(f"- {portfolio_id}: {portfolio['name']}")

    print("\nAvailable scenarios:")
    for scenario_id, scenario in SCENARIOS.items():
        print(f"- {scenario_id}: {scenario.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a RiskLens Alpha portfolio shock simulation.")

    parser.add_argument(
        "--portfolio",
        default="ai_growth_sample",
        help="Sample portfolio ID to simulate.",
    )
    parser.add_argument(
        "--scenario",
        default="ai_capex_slowdown",
        help="Scenario ID to simulate.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available sample portfolios and scenarios.",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save the simulation result as a JSON artifact.",
    )
    parser.add_argument(
        "--output",
        default="reports/json/latest_simulation.json",
        help="Output path for JSON result when --save-json is used.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.list:
        print_available_options()
    else:
        simulation_result = run_simulation(
            portfolio_id=args.portfolio,
            scenario_id=args.scenario,
        )
        print_result(simulation_result)

        if args.save_json:
            saved_path = save_result_json(simulation_result, args.output)
            print(f"Saved JSON result to: {saved_path}")
