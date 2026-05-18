from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class PortfolioModel(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_label: Mapped[str] = mapped_column(String(100), default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    holdings: Mapped[list["HoldingModel"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )

    simulation_runs: Mapped[list["SimulationRunModel"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )


class HoldingModel(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_basis: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    portfolio: Mapped["PortfolioModel"] = relationship(back_populates="holdings")


class WatchlistItemModel(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SimulationRunModel(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(200), nullable=False)
    vulnerability_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    portfolio: Mapped["PortfolioModel"] = relationship(back_populates="simulation_runs")


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    simulation_run_id: Mapped[int] = mapped_column(ForeignKey("simulation_runs.id"), nullable=False)
    html_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RiskTimelinePointModel(Base):
    __tablename__ = "risk_timeline_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), nullable=False, index=True)
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    scenario_name: Mapped[str] = mapped_column(String(200), nullable=False)
    vulnerability_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    hidden_concentration_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_lower: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_upper: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="simulation")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
