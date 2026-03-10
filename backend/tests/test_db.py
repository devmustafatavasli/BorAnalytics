import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db.models import Country, Product

import os

# Use an in-memory SQLite database for testing instead of Postgres
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_country(db):
    new_country = Country(iso3="TST", name="Test Country", region="Test Region")
    db.add(new_country)
    db.commit()
    
    country = db.query(Country).filter(Country.iso3 == "TST").first()
    assert country is not None
    assert country.name == "Test Country"

def test_create_product(db):
    new_product = Product(hs_code="0000", name="Test Product", category="Test")
    db.add(new_product)
    db.commit()
    
    product = db.query(Product).filter(Product.hs_code == "0000").first()
    assert product is not None
    assert product.name == "Test Product"
