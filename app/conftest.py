from fastapi import status
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session
from app.main import app
from app.core.database import get_session
from app.core.enums import ProductType

sqlite_url = "sqlite://"

engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="customer")
def customer(client):
    response = client.post(
        "/customers/",
        json={
            "first_name": "Pepe",
            "last_name": "Perez",
            "birth_date": "2000-12-12",
            "email": "example@example.com"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

@pytest.fixture(name="membership")
def membership(client):
    response = client.post(
        "/memberships/",
        json={
            "name": "Premium",
            "max_days_per_week": 5,
            "points_multiplier": 1.5
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

@pytest.fixture(name="customer_with_membership")
def customer_with_membership(client, customer, membership):
    response = client.post(
        f"/customers/{customer['id']}/membership/{membership['id']}"
    )
    assert response.status_code == status.HTTP_201_CREATED
    return customer

@pytest.fixture(name="attendance")
def attendance(client, customer_with_membership):
    response = client.post(
        "/attendances/",
        json={"customer_id": customer_with_membership["id"]}
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

@pytest.fixture(name="checkout_attendance")
def checkout_attendance(client, attendance):
    attendance_id = attendance["id"]
    response = client.patch(f"/attendances/{attendance_id}/checkout/")
    assert response.status_code == status.HTTP_200_OK
    return attendance_id

@pytest.fixture(name="product")
def product(client):
    response = client.post(
        "/shop/",
        json={
            "name": "Barra energética",
            "description": "Avena",
            "product_type": ProductType.POINTS.value,
            "price": 500,
            "stock": 20
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()