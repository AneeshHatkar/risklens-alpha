from sqlalchemy.orm import Session

from backend.app.models import WatchlistItemModel
from backend.app.services.asset_metadata import get_asset_metadata, normalize_ticker


def add_watchlist_item(
    db: Session,
    ticker: str,
    name: str | None = None,
    notes: str | None = None,
) -> WatchlistItemModel:
    clean_ticker = normalize_ticker(ticker)

    existing = (
        db.query(WatchlistItemModel)
        .filter(WatchlistItemModel.ticker == clean_ticker)
        .first()
    )

    if existing:
        return existing

    metadata = get_asset_metadata(clean_ticker)
    display_name = name or (metadata["name"] if metadata else clean_ticker)

    item = WatchlistItemModel(
        ticker=clean_ticker,
        name=display_name,
        notes=notes,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def list_watchlist_items(db: Session) -> list[WatchlistItemModel]:
    return (
        db.query(WatchlistItemModel)
        .order_by(WatchlistItemModel.created_at.desc())
        .all()
    )


def delete_watchlist_item(db: Session, item_id: int) -> bool:
    item = (
        db.query(WatchlistItemModel)
        .filter(WatchlistItemModel.id == item_id)
        .first()
    )

    if item is None:
        return False

    db.delete(item)
    db.commit()

    return True


def watchlist_item_to_dict(item: WatchlistItemModel) -> dict:
    return {
        "id": item.id,
        "ticker": item.ticker,
        "name": item.name,
        "notes": item.notes,
        "created_at": item.created_at.isoformat(),
    }
