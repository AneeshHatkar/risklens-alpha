from collections import defaultdict

from backend.app.schemas import FactorExposure, Portfolio


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def calculate_hhi_concentration(portfolio: Portfolio) -> float:
    return sum(holding.weight**2 for holding in portfolio.holdings)


def calculate_theme_overlap(
    portfolio: Portfolio,
    exposures: list[FactorExposure],
    minimum_exposure: float = 0.55,
) -> dict[str, float]:
    weights = {holding.ticker: holding.weight for holding in portfolio.holdings}
    theme_scores = defaultdict(float)

    for exposure in exposures:
        if exposure.score >= minimum_exposure:
            theme_scores[exposure.factor] += weights.get(exposure.ticker, 0.0) * exposure.score

    return dict(sorted(theme_scores.items(), key=lambda item: item[1], reverse=True))


def calculate_hidden_concentration(
    portfolio: Portfolio,
    exposures: list[FactorExposure],
) -> dict:
    hhi = calculate_hhi_concentration(portfolio)
    theme_overlap = calculate_theme_overlap(portfolio, exposures)

    top_themes = list(theme_overlap.items())[:5]
    top_theme_score = top_themes[0][1] if top_themes else 0.0
    top_three_theme_score = sum(score for _, score in top_themes[:3])

    # HHI captures direct portfolio concentration.
    # Theme overlap captures hidden factor concentration.
    direct_concentration = clamp(hhi / 0.50)
    factor_concentration = clamp(top_three_theme_score / 1.75)

    hidden_score = round(
        100 * clamp(0.40 * direct_concentration + 0.60 * factor_concentration)
    )

    dominant_themes = [
        {
            "factor": factor,
            "weighted_exposure": round(score, 4),
        }
        for factor, score in top_themes
    ]

    explanation = build_hidden_concentration_explanation(
        portfolio=portfolio,
        hidden_score=hidden_score,
        dominant_themes=dominant_themes,
    )

    return {
        "score": hidden_score,
        "level": hidden_concentration_level(hidden_score),
        "direct_hhi": round(hhi, 4),
        "dominant_themes": dominant_themes,
        "explanation": explanation,
    }


def hidden_concentration_level(score: int) -> str:
    if score <= 30:
        return "low"
    if score <= 60:
        return "moderate"
    if score <= 80:
        return "high"
    return "severe"


def build_hidden_concentration_explanation(
    portfolio: Portfolio,
    hidden_score: int,
    dominant_themes: list[dict],
) -> str:
    holding_count = len(portfolio.holdings)
    theme_names = [item["factor"] for item in dominant_themes[:3]]

    if not theme_names:
        return (
            f"The portfolio has {holding_count} holdings, but there is not enough factor "
            f"mapping data to identify strong hidden concentration."
        )

    themes_text = ", ".join(theme_names)

    return (
        f"The portfolio has {holding_count} holdings, but the hidden concentration score is "
        f"{hidden_score}/100 because multiple holdings share exposure to {themes_text}. "
        f"This means the portfolio may be less diversified by risk theme than it appears by ticker count."
    )
