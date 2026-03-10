import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from db.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.anyio
async def test_get_exports_success(async_client):
    response = await async_client.get("/api/exports")
    assert response.status_code == 200
    # Even if empty, it should be a list
    assert isinstance(response.json(), list)

@pytest.mark.anyio
async def test_get_exports_with_invalid_year(async_client):
    response = await async_client.get("/api/exports?year=abc")
    assert response.status_code == 422 # Validation error

@pytest.mark.anyio
async def test_get_demand_prediction_not_found(async_client):
    # Testing for a non-existent country/product combo
    response = await async_client.get("/api/predictions/demand?product_hs_code=000&country_iso3=XYZ")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_get_demand_invalid_horizon(async_client):
    response = await async_client.get("/api/predictions/demand?product_hs_code=2528&country_iso3=TUR&horizon=10")
    assert response.status_code == 422
