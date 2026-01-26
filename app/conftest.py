from fastapi import status
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session
from datetime import datetime, timezone, timedelta
from app.main import app
from app.core.database import get_session
from app.core.enums import ProductType
from app.attendances.models import Attendance
from app.attendances.services import finalize_attendance, apply_attendance_points
from app.shop.models import Product
from app.customers.models import Customer

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

import pytest

@pytest.fixture(name="customer_with_credentials")
def customer_with_credentials(client):
    payload = {
        "first_name": "Pepe",
        "last_name": "Perez",
        "birth_date": "2000-12-12",
        "email": "example@example.com",
        "password": "password123"
    }

    response = client.post("/customers/", json=payload)
    assert response.status_code == 201

    return {
        "customer": response.json(),
        "email": payload["email"],
        "password": payload["password"],
    }


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



#------ TESTING PARA REDEMPTION ------#
@pytest.fixture(name="customer_with_75_points")
def customer_with_75_points(client, session, customer_with_membership):
    customer = session.get(Customer, customer_with_membership["id"])
    ATTENDANCES = 5

    for _ in range(ATTENDANCES):
        #Crear asistencia
        response = client.post(
            "/attendances/",
            json={"customer_id": customer_with_membership["id"]}
        )

        assert response.status_code == 201, response.json()

        attendance_id = response.json()["id"]

        # traer asistencia desde DB
        attendance = session.get(Attendance, attendance_id)

        # Simular una asistencia válida
        attendance.check_in = datetime.now(timezone.utc) - timedelta(minutes=60)
        attendance.check_out = datetime.now(timezone.utc)

        finalize_attendance(attendance)
        apply_attendance_points(attendance, customer)

        session.commit()

    customer = session.get(Customer, customer_with_membership["id"])

    return customer

@pytest.fixture(name="expensive_product")
def expensive_product(session):
    product = Product(
        name="Producto caro",
        description="ejemplo",
        product_type=ProductType.POINTS,
        price=500,
        stock=5,
        is_active=True
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@pytest.fixture(name="cheap_product")
def cheap_product(session):
    product = Product(
        name="Producto barato",
        description="ejemplo",
        product_type=ProductType.POINTS,
        price=70,
        stock=5,
        is_active=True
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@pytest.fixture(name="product_is_not_active")
def product_is_not_active(session):
    product = Product(
        name="Producto inactivo",
        description="ejemplo",
        product_type=ProductType.POINTS,
        price=50,
        stock=5,
        is_active=False
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@pytest.fixture(name="product_with_money")
def product_with_money(session):
    product = Product(
        name="Producto inactivo",
        description="ejemplo",
        product_type=ProductType.MONEY,
        price=50,
        stock=5,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@pytest.fixture(name="product_without_stock")
def product_without_stock(session):
    product = Product(
        name="Producto sin stock",
        description="ejemplo",
        product_type=ProductType.POINTS,
        price=50,
        stock=0,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


        
