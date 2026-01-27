from fastapi import status
import pytest
from datetime import datetime, timezone, timedelta

from app.core.security import get_password_hash
from app.core.enums import ProductType, RoleEnum
from app.attendances.models import Attendance
from app.attendances.services import finalize_attendance, apply_attendance_points
from app.shop.models import Product
from app.customers.models import Customer
from app.auth.models import User


@pytest.fixture(name="admin_user")
def admin_user(session):
    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role=RoleEnum.ADMIN,
        is_active=True
    )

    session.add(admin)
    session.commit()
    session.refresh(admin)

    return {
        "email": admin.email,
        "password": "admin123"
    }


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

## HASTA ACÁ

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


        
