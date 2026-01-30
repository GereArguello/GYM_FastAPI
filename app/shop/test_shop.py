from fastapi import status
from app.core.enums import ProductType, StatusEnum
from app.helpers import login

def test_create_product_success(client, admin_user):
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
    data = response.json()
    assert "id" in data
    assert data["name"] == "Barra energética"
    assert data["product_type"] == "points"
    assert data["price"] == 500
    assert data["status"] == StatusEnum.ACTIVE

def test_create_unauthorized(client, customer_with_credentials):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

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
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_product_duplicate_name(client, product, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    response = client.post(
        "/shop/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": product["name"],
            "description": "Otra",
            "product_type": ProductType.POINTS.value,
            "price": 600,
            "stock": 10
        }
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Ya existe un producto con ese nombre"

def test_read_product(client, product):
    product_id = product["id"]
    response = client.get(f"/shop/{product_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Barra energética"

def test_patch_product(client, product, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    product_id = product["id"]

    response = client.patch(f"/shop/{product_id}",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"price": 1000}
                            )
    updated_product = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert updated_product["price"] == 1000
    assert product["price"] != updated_product["price"]

def test_soft_delete(client, product, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    product_id = product["id"]

    response_delete = client.delete(f"/shop/{product_id}",
                                    headers={"Authorization": f"Bearer {token}"})
    
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT

    # Consultar el producto nuevamente
    response = client.get(f"/shop/{product_id}",
                          headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == StatusEnum.INACTIVE

def test_activate_product(client, product, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    product_id = product["id"]

    response_delete = client.delete(f"/shop/{product_id}",
                                    headers={"Authorization": f"Bearer {token}"})
    
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT

    response = client.patch(f"/shop/{product_id}/activate",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == StatusEnum.ACTIVE

def test_read_inactive_product_as_non_admin_returns_404(
    client, product, admin_user, customer_with_credentials
):
    # Desactivar producto
    admin_token = login(client, admin_user["email"], admin_user["password"])
    client.delete(
        f"/shop/{product['id']}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Intentar leerlo como usuario normal
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    response = client.get(
        f"/shop/{product['id']}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_list_products_does_not_include_inactive_for_public(
    client, product, admin_user
):
    admin_token = login(client, admin_user["email"], admin_user["password"])

    # Soft delete
    client.delete(
        f"/shop/{product['id']}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    response = client.get("/shop/")
    assert response.status_code == status.HTTP_200_OK

    ids = [p["id"] for p in response.json()["items"]]
    assert product["id"] not in ids

def test_list_products_paginated(client, admin_user, product):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.get(
        "/shop?page=1&size=5",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    # estructura de paginación
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "size" in body

    # comportamiento esperado
    assert body["page"] == 1
    assert body["size"] == 5
    assert isinstance(body["items"], list)