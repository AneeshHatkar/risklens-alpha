import argparse
import json
from pathlib import Path

from backend.app.config import get_settings

from backend.app.schemas import SimulationResult
from backend.app.services.agent_debate import run_agent_debate
from backend.app.services.factor_mapper import map_factors
from backend.app.services.hidden_concentration import calculate_hidden_concentration
from backend.app.services.market_metrics import compute_market_metrics
from backend.app.services.confidence_engine import calculate_confidence_interval
from backend.app.services.portfolio_parser import normalize_portfolio
from backend.app.services.risk_scoring import score_portfolio
from backend.app.services.scenario_generator import SCENARIOS, get_scenario
from backend.app.services.scenario_comparison import compare_scenarios
from backend.app.services.what_if import compare_what_if_portfolios


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
    use_market_data: bool = False,
) -> SimulationResult:
    raw_portfolio = load_sample_portfolio(portfolio_id)
    portfolio = normalize_portfolio(raw_portfolio)
    scenario = get_scenario(scenario_id)

    market_metrics = None
    if use_market_data:
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
        market_metrics=market_metrics,
        confidence_interval=confidence_interval,
        hidden_concentration=hidden_concentration,
    )




def run_scenario_comparison(
    portfolio_id: str = "ai_growth_sample",
    use_market_data: bool = False,
) -> list[dict]:
    raw_portfolio = load_sample_portfolio(portfolio_id)
    portfolio = normalize_portfolio(raw_portfolio)

    market_metrics = None
    if use_market_data:
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


def print_scenario_comparison(portfolio_id: str, results: list[dict]) -> None:
    print("\n" + "=" * 72)
    print("RiskLens Alpha Scenario Comparison")
    print("=" * 72)
    print(f"\nPortfolio ID: {portfolio_id}")

    for index, item in enumerate(results, start=1):
        holdings = ", ".join(item["most_vulnerable_holdings"]) or "none"
        factors = ", ".join(item["dominant_factors"][:3]) or "limited mapped factors"

        print(
            f"\n{index}. {item['scenario_name']} "
            f"— {item['vulnerability_score']}/100 ({item['risk_level'].upper()})"
        )
        print(f"   Top factors : {factors}")
        print(f"   Holdings    : {holdings}")

    print("=" * 72 + "\n")



def run_what_if_demo(
    portfolio_id: str = "ai_growth_sample",
    scenario_id: str = "ai_capex_slowdown",
    use_market_data: bool = False,
) -> dict:
    raw_base = load_sample_portfolio(portfolio_id)
    base_portfolio = normalize_portfolio(raw_base)
    scenario = get_scenario(scenario_id)

    what_if_raw = {
        "name": f"What-if version of {base_portfolio.name}",
        "holdings": [
            {"ticker": "NVDA", "weight": 0.20},
            {"ticker": "MSFT", "weight": 0.25},
            {"ticker": "AAPL", "weight": 0.25},
            {"ticker": "SPY", "weight": 0.30},
        ],
    }
    what_if_portfolio = normalize_portfolio(what_if_raw)

    market_metrics = None
    if use_market_data:
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


def print_what_if_result(result: dict) -> None:
    print("\n" + "=" * 72)
    print("RiskLens Alpha What-if Portfolio Analysis")
    print("=" * 72)

    print(f"\nScenario: {result['scenario_name']}")

    print("\nBase Portfolio:")
    print(f"- Score: {result['base']['vulnerability_score']}/100 ({result['base']['risk_level'].upper()})")
    print(f"- Hidden concentration: {result['base']['hidden_concentration']['score']}/100")

    print("\nWhat-if Portfolio:")
    print(f"- Score: {result['what_if']['vulnerability_score']}/100 ({result['what_if']['risk_level'].upper()})")
    print(f"- Hidden concentration: {result['what_if']['hidden_concentration']['score']}/100")

    print("\nChange:")
    print(f"- Vulnerability score delta: {result['score_delta']}")
    print(f"- Hidden concentration delta: {result['hidden_concentration_delta']}")
    print(result["interpretation"])

    print("\nSafety Note:")
    print(result["safety_note"])
    print("=" * 72 + "\n")

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

    if result.confidence_interval:
        interval = result.confidence_interval
        print("\n--- Confidence Interval ---")
        print(f"Range      : {interval['lower']}–{interval['upper']}")
        print(f"Confidence : {interval['confidence']} ({interval['label']})")

    if result.hidden_concentration:
        hidden = result.hidden_concentration
        print("\n--- Hidden Concentration ---")
        print(f"Score: {hidden['score']}/100 ({hidden['level']})")
        print("Dominant overlap themes:")
        for theme in hidden["dominant_themes"][:5]:
            print(f"- {theme['factor']}: {theme['weighted_exposure']}")
        print(hidden["explanation"])

    if result.market_metrics:
        portfolio_metrics = result.market_metrics["portfolio_metrics"]
        print("\n--- Market Metrics ---")
        print(f"Portfolio Volatility     : {portfolio_metrics['portfolio_volatility']}")
        print(f"Avg Pairwise Correlation : {portfolio_metrics['average_pairwise_correlation']}")
        print(f"Benchmark                : {portfolio_metrics['benchmark']}")

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
        "--use-market-data",
        action="store_true",
        help="Include live market metrics from yfinance in the simulation result.",
    )
    parser.add_argument(
        "--compare-scenarios",
        action="store_true",
        help="Run the selected portfolio against every predefined scenario.",
    )
    parser.add_argument(
        "--what-if-demo",
        action="store_true",
        help="Run a built-in what-if portfolio adjustment demo.",
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
    elif args.compare_scenarios:
        comparison_results = run_scenario_comparison(
            portfolio_id=args.portfolio,
            use_market_data=args.use_market_data,
        )
        print_scenario_comparison(args.portfolio, comparison_results)

        if args.save_json:
            saved_path = Path(args.output)
            saved_path.parent.mkdir(parents=True, exist_ok=True)
            with open(saved_path, "w", encoding="utf-8") as file:
                json.dump(comparison_results, file, indent=2)
            print(f"Saved scenario comparison JSON to: {saved_path}")
    elif args.what_if_demo:
        what_if_result = run_what_if_demo(
            portfolio_id=args.portfolio,
            scenario_id=args.scenario,
            use_market_data=args.use_market_data,
        )
        print_what_if_result(what_if_result)

        if args.save_json:
            saved_path = Path(args.output)
            saved_path.parent.mkdir(parents=True, exist_ok=True)
            with open(saved_path, "w", encoding="utf-8") as file:
                json.dump(what_if_result, file, indent=2)
            print(f"Saved what-if JSON to: {saved_path}")
    else:
        simulation_result = run_simulation(
            portfolio_id=args.portfolio,
            scenario_id=args.scenario,
            use_market_data=args.use_market_data,
        )
        print_result(simulation_result)

        if args.save_json:
            saved_path = save_result_json(simulation_result, args.output)
            print(f"Saved JSON result to: {saved_path}")
