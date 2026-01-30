import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.attendances.models import Attendance
from app.attendances.services import finalize_attendance, apply_attendance_points
from app.customers.models import Customer
from app.helpers import login
from app.shop.models import Product
from app.core.enums import ProductType, StatusEnum


## ----- FIXTURES PARA REDEMPTIONS ---- ##
@pytest.fixture(name="customer_with_75_points")
def customer_with_75_points(client, session, customer_with_membership):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    customer = session.get(Customer, c["customer"]["id"])

    ATTENDANCES = 5

    for day in range(ATTENDANCES):
        #Crear asistencia
        response = client.post(
            "/attendances/",
            headers={"Authorization": f"Bearer {token}"},
            json={}
        )

        assert response.status_code == 201, response.json()

        attendance_id = response.json()["id"]

        # traer asistencia desde DB
        attendance = session.get(Attendance, attendance_id)

        base_time = datetime.now(timezone.utc) + timedelta(days=day)

        # Simular una asistencia válida
        attendance.check_in = base_time
        attendance.check_out = base_time + timedelta(minutes=35)

        finalize_attendance(attendance)
        apply_attendance_points(attendance, customer)

    session.commit()
    session.refresh(customer)

    assert customer.points_balance == 75
    
    return customer

@pytest.fixture(name="product_is_not_active")
def product_is_not_active(session):
    product = Product(
        name="Producto inactivo",
        description="ejemplo",
        product_type=ProductType.POINTS,
        price=50,
        stock=5,
        status=StatusEnum.INACTIVE
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

@pytest.fixture(name="expensive_product")
def expensive_product(session):
    product = Product(
        name="Producto caro",
        description="ejemplo",
        product_type=ProductType.POINTS,
        price=500,
        stock=5,
        status=StatusEnum.ACTIVE
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
        status=StatusEnum.ACTIVE
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@pytest.fixture(name="redemption")
def redemption(client,
               customer_with_credentials,
               customer_with_75_points,
               cheap_product):
    
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    r = client.post(
        f"/redemptions/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": cheap_product.id,
            "quantity": 1
        }
    )

    assert r.status_code == status.HTTP_201_CREATED
    return r.json()