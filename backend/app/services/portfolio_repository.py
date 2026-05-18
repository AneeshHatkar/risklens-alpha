from sqlalchemy.orm import Session

from backend.app.models import HoldingModel, PortfolioModel
from backend.app.schemas import Holding, Portfolio, PortfolioCreateRequest


def create_portfolio(db: Session, request: PortfolioCreateRequest) -> PortfolioModel:
    portfolio = PortfolioModel(
        name=request.name,
        owner_label=request.owner_label,
    )

    for holding in request.holdings:
        portfolio.holdings.append(
            HoldingModel(
                ticker=holding.ticker.upper(),
                weight=holding.weight,
                shares=holding.shares,
                cost_basis=holding.cost_basis,
            )
        )

    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    return portfolio


def list_portfolios(db: Session) -> list[PortfolioModel]:
    return (
        db.query(PortfolioModel)
        .order_by(PortfolioModel.created_at.desc())
        .all()
    )


def get_portfolio_by_id(db: Session, portfolio_id: int) -> PortfolioModel | None:
    return (
        db.query(PortfolioModel)
        .filter(PortfolioModel.id == portfolio_id)
        .first()
    )


def delete_portfolio(db: Session, portfolio_id: int) -> bool:
    portfolio = get_portfolio_by_id(db, portfolio_id)

    if portfolio is None:
        return False

    db.delete(portfolio)
    db.commit()

    return True


def portfolio_model_to_schema(portfolio: PortfolioModel) -> Portfolio:
    return Portfolio(
        name=portfolio.name,
        holdings=[
            Holding(
                ticker=holding.ticker,
                weight=holding.weight,
                shares=holding.shares,
                cost_basis=holding.cost_basis,
            )
            for holding in portfolio.holdings
        ],
    )


def portfolio_summary(portfolio: PortfolioModel) -> dict:
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "owner_label": portfolio.owner_label,
        "holding_count": len(portfolio.holdings),
        "created_at": portfolio.created_at.isoformat(),
    }


def portfolio_detail(portfolio: PortfolioModel) -> dict:
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "owner_label": portfolio.owner_label,
        "holdings": [
            {
                "ticker": holding.ticker,
                "weight": holding.weight,
                "shares": holding.shares,
                "cost_basis": holding.cost_basis,
            }
            for holding in portfolio.holdings
        ],
        "created_at": portfolio.created_at.isoformat(),
    }
