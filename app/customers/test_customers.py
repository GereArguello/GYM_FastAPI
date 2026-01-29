from fastapi import status
from app.customers.models import Customer
from app.helpers import login, create_customer
from app.core.enums import StatusEnum

#------- TEST CRUD CUSTOMERS -------#
def test_create_customer_success(client):
    response = client.post(
        "/customers/",
        json={
            "first_name": "Pepe",
            "last_name": "Perez",
            "birth_date": "2000-12-12",
            "email": "example@example.com",
            "password": "password123"
        }
    )
    data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert data["first_name"] == "Pepe"
    assert data["points_balance"] == 0
    assert data["is_active"] == "active"



def test_create_customer_duplicate_email(client):
    client.post(
        "/customers/",
        json={
            "first_name": "Pepe",
            "last_name": "Perez",
            "birth_date": "2000-12-12",
            "email": "example@example.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/customers/",
        json={
            "first_name": "Otro",
            "last_name": "Otro",
            "birth_date": "2001-12-12",
            "email": "example@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_list_customers_as_admin(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.get(
        "/customers/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

def test_customer_cannot_list_customers(client, customer_with_credentials):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    response = client.get(
        "/customers/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403

def test_read_customer_as_admin(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])

    customer = create_customer(
        client,
        email="example2@example.com"
    )

    response = client.get(
        f"/customers/{customer['id']}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK

def test_customer_cannot_read_another_customer(client, customer_with_credentials):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    customer = create_customer(
        client,
        email="example2@example.com"
    )

    response = client.get(
        f"/customers/{customer['id']}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN



def test_update_customer(client, customer_with_credentials):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    #Update
    patch_response = client.patch(
        "/customers/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "Pablo"}
    )
    assert patch_response.status_code == status.HTTP_200_OK

    updated_customer = patch_response.json()

    #Testear cambio
    assert updated_customer["first_name"] == "Pablo"

    #Otros valores
    assert updated_customer["last_name"] == "Perez"

def test_admin_cannot_update_customer_me(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.patch(
        "/customers/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "AdminHack"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_customer(client, session, customer_with_credentials):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    response_delete = client.delete(f"/customers/me/deactivate",
                                    headers={"Authorization": f"Bearer {token}"})

    assert response_delete.status_code == status.HTTP_204_NO_CONTENT
    #Validamos que el customer fue eliminado
    customer_id = c["customer"]["id"]
    deleted_customer = session.get(Customer, customer_id)
    assert deleted_customer.is_active == StatusEnum.INACTIVE

def test_list_customers_paginated(
    client,
    admin_user,
    customer_with_credentials
):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.get(
        "/customers?page=1&size=1",
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
    assert body["size"] == 1
    assert len(body["items"]) <= 1