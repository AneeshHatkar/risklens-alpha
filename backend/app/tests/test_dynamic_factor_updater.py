from backend.app.services.dynamic_factor_updater import (
    calculate_factor_adjustment,
    get_base_factor_exposure,
    run_dynamic_factor_update,
    update_factor_exposure_for_ticker,
)


def test_get_base_factor_exposure_for_known_ticker():
    exposure = get_base_factor_exposure("NVDA", "semiconductors")

    assert exposure["ticker"] == "NVDA"
    assert exposure["factor"] == "semiconductors"
    assert exposure["base_score"] > 0
    assert exposure["exists_in_base_map"] is True


def test_calculate_factor_adjustment_for_matching_narrative():
    narrative = {
        "affected_tickers": ["NVDA"],
        "affected_factors": ["semiconductors"],
        "severity": 0.9,
        "confidence": 0.5,
    }

    result = calculate_factor_adjustment(
        ticker="NVDA",
        factor="semiconductors",
        narrative=narrative,
    )

    assert result["adjustment"] > 0
    assert result["ticker_match"] is True
    assert result["factor_match"] is True


def test_update_factor_exposure_for_ticker_increases_score():
    narratives = [
        {
            "narrative": "semiconductor_export_restriction",
            "display_name": "Semiconductor Export Restriction",
            "affected_tickers": ["NVDA"],
            "affected_factors": ["semiconductors"],
            "severity": 0.9,
            "confidence": 0.5,
            "evidence": ["Export controls increased."],
        }
    ]

    updates = update_factor_exposure_for_ticker(
        ticker="NVDA",
        factors=["semiconductors"],
        narratives=narratives,
    )

    update = updates[0]

    assert update["dynamic_score"] >= update["base_score"]
    assert update["adjustment"] > 0


def test_run_dynamic_factor_update_returns_updates():
    result = run_dynamic_factor_update(
        articles=[
            {
                "title": "NVDA falls after China chip export restrictions",
                "summary": "Investors worry AI accelerator shipments could be limited.",
                "tickers": ["NVDA"],
            }
        ],
        tickers=["NVDA", "AMD"],
    )

    assert result["narrative_count"] == 1
    assert "ticker_updates" in result
    assert "NVDA" in result["ticker_updates"]
    assert "summary" in result
