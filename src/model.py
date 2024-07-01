from sqlalchemy import ForeignKey, Integer, String, Float, Date, DateTime
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Metadata(Base):
    __tablename__ = "meta"
    id = mapped_column(Integer, primary_key=True)
    last_updated = mapped_column(DateTime)
    contracted_hours_updated_month = mapped_column(String, nullable=True)


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
    unit = mapped_column(String, nullable=True)


class UOS(Base):
    __tablename__ = "uos"
    id = mapped_column(Integer, primary_key=True)
    dept_wd_id = mapped_column(String(10), nullable=False)
    dept_name = mapped_column(String, nullable=True)
    month = mapped_column(String(7), nullable=False)
    volume = mapped_column(Float, nullable=False)
    unit = mapped_column(String, nullable=True)


class Budget(Base):
    __tablename__ = "budget"
    id = mapped_column(Integer, primary_key=True)
    dept_wd_id = mapped_column(String(10), nullable=False)
    dept_name = mapped_column(String, nullable=True)
    budget_fte = mapped_column(Float, nullable=False)
    budget_prod_hrs = mapped_column(Float, nullable=False)
    budget_volume = mapped_column(Integer, nullable=False)
    budget_uos = mapped_column(Float, nullable=False)
    budget_prod_hrs_per_uos = mapped_column(Float, nullable=False)
    hourly_rate = mapped_column(Float, nullable=False)


class Hours(Base):
    __tablename__ = "hours"
    id = mapped_column(Integer, primary_key=True)
    month = mapped_column(String(7), nullable=False)
    dept_wd_id = mapped_column(String(10), nullable=False)
    dept_name = mapped_column(String, nullable=True)
    reg_hrs = mapped_column(Float, nullable=False)
    overtime_hrs = mapped_column(Float, nullable=False)
    prod_hrs = mapped_column(Float, nullable=False)
    nonprod_hrs = mapped_column(Float, nullable=False)
    total_hrs = mapped_column(Float, nullable=False)
    total_fte = mapped_column(Float, nullable=False)


class ContractedHours(Base):
    __tablename__ = "contracted_hours"
    id = mapped_column(Integer, primary_key=True)
    dept_wd_id = mapped_column(String(10), nullable=False)
    dept_name = mapped_column(String, nullable=True)
    year = mapped_column(Integer, nullable=False)
    hrs = mapped_column(Float, nullable=True)
    ttl_dept_hrs = mapped_column(Float, nullable=False)


class HoursByPayPeriod(Base):
    __tablename__ = "hours_by_pay_period"
    id = mapped_column(Integer, primary_key=True)
    pay_period = mapped_column(String(7), nullable=False)
    start_date = mapped_column(DateTime)
    dept_wd_id = mapped_column(String(10), nullable=False)
    dept_name = mapped_column(String, nullable=True)
    reg_hrs = mapped_column(Float, nullable=False)
    overtime_hrs = mapped_column(Float, nullable=False)
    prod_hrs = mapped_column(Float, nullable=False)
    nonprod_hrs = mapped_column(Float, nullable=False)
    total_hrs = mapped_column(Float, nullable=False)
    total_fte = mapped_column(Float, nullable=False)


class IncomeStmt(Base):
    __tablename__ = "income_stmt"
    id = mapped_column(Integer, primary_key=True)
    month = mapped_column(String(7), nullable=False)
    ledger_acct = mapped_column(String, nullable=False)
    dept_wd_id = mapped_column(String(10), nullable=False)
    dept_name = mapped_column(String, nullable=True)
    spend_category = mapped_column(String, nullable=True)
    revenue_category = mapped_column(String, nullable=True)
    actual = mapped_column(Float, nullable=False)
    budget = mapped_column(Float, nullable=False)
    actual_ytd = mapped_column(Float, nullable=False)
    budget_ytd = mapped_column(Float, nullable=False)
