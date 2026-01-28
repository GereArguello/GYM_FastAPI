import pytest
from fastapi import status
from app.core.enums import ProductType
from app.helpers import login

@pytest.fixture(name="product")
def product(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    response = client.post(
        "/shop/",
        headers={"Authorization": f"Bearer {token}"},
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