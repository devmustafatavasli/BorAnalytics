from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    iso3 = Column(String(3), unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    region = Column(String)

    exports = relationship("Export", back_populates="country")
    predictions = relationship("Prediction", back_populates="country")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    hs_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)

    exports = relationship("Export", back_populates="product")
    productions = relationship("Production", back_populates="product")
    predictions = relationship("Prediction", back_populates="product")

class Export(Base):
    __tablename__ = "exports"

    year = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("countries.id", ondelete="CASCADE"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    volume_tons = Column(Float, nullable=False)
    value_usd = Column(Float, nullable=False)
    anomaly_flag = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)

    country = relationship("Country", back_populates="exports")
    product = relationship("Product", back_populates="exports")

class Production(Base):
    __tablename__ = "production"

    year = Column(Integer, primary_key=True)
    facility = Column(String, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    volume_tons = Column(Float, nullable=False)

    product = relationship("Product", back_populates="productions")

class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_type = Column(String, nullable=False, index=True)
    trained_at = Column(DateTime, default=datetime.utcnow)
    mae = Column(Float)
    rmse = Column(Float)
    r2 = Column(Float)
    params_json = Column(JSON)

    predictions = relationship("Prediction", back_populates="model_run")

class Prediction(Base):
    __tablename__ = "predictions"

    country_id = Column(Integer, ForeignKey("countries.id", ondelete="CASCADE"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    year = Column(Integer, primary_key=True)
    model_run_id = Column(Integer, ForeignKey("model_runs.id", ondelete="CASCADE"), primary_key=True)
    
    predicted_value = Column(Float, nullable=False)
    lower_ci = Column(Float)
    upper_ci = Column(Float)

    country = relationship("Country", back_populates="predictions")
    product = relationship("Product", back_populates="predictions")
    model_run = relationship("ModelRun", back_populates="predictions")
