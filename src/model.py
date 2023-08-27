from sqlalchemy import ForeignKey, Integer, String, Float, Date, DateTime
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Metadata(Base):
    __tablename__ = "meta"
    id = mapped_column(Integer, primary_key=True)
    last_updated = mapped_column(DateTime)


class SourceMetadata(Base):
    __tablename__ = "sources_meta"
    id = mapped_column(Integer, primary_key=True)
    filename = mapped_column(String, nullable=False)
    modified = mapped_column(DateTime, nullable=False)


class Volume(Base):
    __tablename__ = "volumes"
    id = mapped_column(Integer, primary_key=True)
    dept_wd_id = mapped_column(String(10), nullable=False)
    dept_name = mapped_column(String, nullable=True)
    month = mapped_column(String(7), nullable=False)
    volume = mapped_column(Integer, nullable=False)


class BudgetedHoursPerVolume(Base):
    __tablename__ = "budgeted_hours_per_volume"
    id = mapped_column(Integer, primary_key=True)
    dept_wd_id = mapped_column(String(10), nullable=False)
    dept_name = mapped_column(String, nullable=True)
    budgeted_hours_per_volume = mapped_column(Float, nullable=False)


class IncomeStmt(Base):
    __tablename__ = "income_stmt"
    id = mapped_column(Integer, primary_key=True)
    month = mapped_column(String(7), nullable=False)
    ledger_acct = mapped_column(String, nullable=False)
    cost_center = mapped_column(String, nullable=True)
    spend_category = mapped_column(String, nullable=True)
    revenue_category = mapped_column(String, nullable=True)
    actual = mapped_column(Float, nullable=False)
    budget = mapped_column(Float, nullable=False)
    actual_ytd = mapped_column(Float, nullable=False)
    budget_ytd = mapped_column(Float, nullable=False)
