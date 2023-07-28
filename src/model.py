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


class Dept(Base):
    __tablename__ = "depts"
    id = mapped_column(Integer, primary_key=True)
    wd_id = mapped_column(String(10), nullable=False, unique=True, index=True)
    name = mapped_column(String, nullable=False)


class Volume(Base):
    __tablename__ = "volumes"
    id = mapped_column(Integer, primary_key=True)
    period = mapped_column(Date, nullable=False)
    volume = mapped_column(Integer)

    dept = relationship("Dept", back_populates="volumes")
