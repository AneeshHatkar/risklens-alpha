from backend.app.main import run_simulation


def main():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
        use_market_data=False,
    )

    disagreement = result.agent_disagreement

    print("\nRiskLens Alpha Agent Disagreement")
    print("=" * 56)
    print(f"Portfolio: {result.portfolio_name}")
    print(f"Scenario: {result.scenario.name}")

    if not disagreement:
        print("No disagreement result found.")
        return

    print(f"Score: {disagreement['score']}/100")
    print(f"Label: {disagreement['label']}")
    print(f"Confidence spread: {disagreement['confidence_spread']}")
    print(f"Holding disagreement: {disagreement['holding_disagreement']}")
    print(f"Risk-theme disagreement: {disagreement['risk_theme_disagreement']}")
    print(f"Summary: {disagreement['summary']}")


if __name__ == "__main__":
    main()
