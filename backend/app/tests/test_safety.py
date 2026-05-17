from backend.app.main import run_simulation


FORBIDDEN_PHRASES = [
    "you should buy",
    "you should sell",
    "guaranteed return",
    "will definitely go up",
    "will definitely crash",
]


def test_simulation_summary_avoids_financial_advice():
    result = run_simulation(
        portfolio_id="ai_growth_sample",
        scenario_id="ai_capex_slowdown",
    )

    text = " ".join(
        [
            result.summary,
            result.disclaimer,
            *[agent.thesis for agent in result.agent_opinions],
        ]
    ).lower()

    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in text


def test_disclaimer_is_present():
    result = run_simulation()

    assert "not financial advice" in result.disclaimer.lower()
    assert "does not recommend buying or selling" in result.disclaimer.lower()
