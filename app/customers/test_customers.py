from fastapi import status
from datetime import date
from app.customers.models import Customer

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

def test_read_customer(client):
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
    customer_id: int = response.json()["id"]
    response_read = client.get(f"/customers/{customer_id}")

    assert response_read.status_code == status.HTTP_200_OK
    assert response_read.json()["first_name"] == "Pepe"

def test_update_customer(client):
    #Create
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
    customer = response.json()
    customer_id = customer["id"]
    #Update
    patch_response = client.patch(
        f"/customers/{customer_id}",
        json={"first_name": "Pablo"}
    )
    assert patch_response.status_code == status.HTTP_200_OK

    updated_customer = patch_response.json()

    #Testear cambio
    assert updated_customer["first_name"] == "Pablo"

    #Otros valores
    assert updated_customer["last_name"] == "Perez"


def test_delete_customer(client, session):
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
    customer_id = response.json()["id"]
    response_delete = client.delete(f"/customers/{customer_id}")
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT
    #Validamos que el customer fue eliminado
    deleted_customer = session.get(Customer, customer_id)
    assert deleted_customer is None

#------- TEST CRUD CUSTOMERMEMBERSHIP -------#

def test_create_customer_membership(client):
    # Create customer
    response_customer = client.post(
        "/customers/",
        json={
            "first_name": "Pepe",
            "last_name": "Perez",
            "birth_date": "2000-12-12",
            "email": "example@example.com",
            "password": "password123"
        }
    )
    assert response_customer.status_code == status.HTTP_201_CREATED
    customer_id = response_customer.json()["id"]

    # Create membership
    response_membership = client.post(
        "/memberships/",
        json={
            "name": "Premium",
            "max_days_per_week": 5,
            "points_multiplier": 1.5
        }
    )
    assert response_membership.status_code == status.HTTP_201_CREATED
    membership_id = response_membership.json()["id"]

    response = client.post(
        f"/customers/{customer_id}/membership/{membership_id}"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["customer_id"] == customer_id
    assert response.json()["membership_id"] == membership_id
    assert response.json()["is_active"] is True
    assert response.json()["start_date"] == date.today().isoformat()

def test_assign_same_membership_twice_returns_400(client):
    # Create customer
    response_customer = client.post(
        "/customers/",
        json={
            "first_name": "Pepe",
            "last_name": "Perez",
            "birth_date": "2000-12-12",
            "email": "example@example.com",
            "password": "password123"
        }
    )
    assert response_customer.status_code == status.HTTP_201_CREATED
    customer_id = response_customer.json()["id"]

    # Create membership
    response_membership = client.post(
        "/memberships/",
        json={
            "name": "Premium",
            "max_days_per_week": 5,
            "points_multiplier": 1.5
        }
    )
    assert response_membership.status_code == status.HTTP_201_CREATED
    membership_id = response_membership.json()["id"]

    client.post(f"/customers/{customer_id}/membership/{membership_id}")

    response = client.post(
        f"/customers/{customer_id}/membership/{membership_id}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_reassign_membership_deactivates_previous(client):
    # Create customer
    response_customer = client.post(
        "/customers/",
        json={
            "first_name": "Pepe",
            "last_name": "Perez",
            "birth_date": "2000-12-12",
            "email": "example@example.com",
            "password": "password123"
        }
    )
    assert response_customer.status_code == status.HTTP_201_CREATED
    customer_id = response_customer.json()["id"]

    # Create first membership
    response_membership_a = client.post(
        "/memberships/",
        json={
            "name": "Premium",
            "max_days_per_week": 5,
            "points_multiplier": 1.5
        }
    )
    assert response_membership_a.status_code == status.HTTP_201_CREATED
    membership_a = response_membership_a.json()["id"]

    # Create second membership
    response_membership_b = client.post(
        "/memberships/",
        json={
            "name": "Basic",
            "max_days_per_week": 3,
            "points_multiplier": 1.0
        }
    )
    assert response_membership_b.status_code == status.HTTP_201_CREATED
    membership_b = response_membership_b.json()["id"]

    # Asignamos primer membership
    response_assign_a = client.post(
        f"/customers/{customer_id}/membership/{membership_a}"
    )
    assert response_assign_a.status_code == status.HTTP_201_CREATED

    # Reasignamos a segundo membership > debe desactivar la primera
    response_assign_b = client.post(
        f"/customers/{customer_id}/membership/{membership_b}"
    )
    assert response_assign_b.status_code == status.HTTP_201_CREATED

    # membership activa debe ser la segunda
    response_active = client.get(
        f"/customers/{customer_id}/membership/active"
    )
    assert response_active.status_code == status.HTTP_200_OK
    assert response_active.json()["membership_id"] == membership_b

def test_get_active_membership_returns_404_if_never_assigned(client):
    response_customer = client.post(
        "/customers/",
        json={
            "first_name": "Pepe",
            "last_name": "Perez",
            "birth_date": "2000-12-12",
            "email": "example@example.com",
            "password": "password123"
        }
    )
    customer_id = response_customer.json()["id"]

    response = client.get(
        f"/customers/{customer_id}/membership/active"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
