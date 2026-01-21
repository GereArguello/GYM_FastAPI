from fastapi import status
from app.core.enums import ProductType

def test_create_product_success(client):
    response = client.post(
        "/shop/",
        json={
            "name": "Proteína Whey",
            "description": "Chocolate",
            "product_type": ProductType.POINTS.value,
            "price": 12000,
            "stock": 10
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["name"] == "Proteína Whey"
    assert data["product_type"] == "points"
    assert data["price"] == 12000
    assert data["is_active"] is True

def test_create_product_negative_price(client):
    response = client.post(
        "/shop/",
        json={
            "name": "Proteína Whey",
            "description": "Chocolate",
            "product_type": ProductType.POINTS.value,
            "price": -1,
            "stock": 10
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "El precio no puede ser negativo"

def test_create_product_duplicate_name(client, product):
    response = client.post(
        "/shop/",
        json={
            "name": product["name"],
            "description": "Otra",
            "product_type": ProductType.POINTS.value,
            "price": 600,
            "stock": 10
        }
    )

    assert response.status_code == status.HTTP_409_CONFLICT

def test_read_product(client, product):
    product_id = product["id"]
    response = client.get(f"/shop/{product_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Barra energética"

def test_patch_product(client, product):
    product_id = product["id"]

    response = client.patch(f"/shop/{product_id}",json={
        "price": 1000
    })
    updated_product = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert updated_product["price"] == 1000
    assert product["price"] != updated_product["price"]

def test_soft_delete(client, product):
    product_id = product["id"]

    response_delete = client.delete(f"/shop/{product_id}")
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT

    # Consultar el producto nuevamente
    response = client.get(f"/shop/{product_id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["is_active"] is False

def test_activate_product(client, product):
    product_id = product["id"]

    response_delete = client.delete(f"/shop/{product_id}")
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT

    response = client.patch(f"/shop/{product_id}/activate")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_active"] == True

