from fastapi import status
from sqlmodel import select
from datetime import date
from app.helpers import login
from app.core.enums import MembershipStatusEnum
from app.customers.services import obtener_ultimo_dia
from app.customers.models import CustomerMembership

#------- TEST CRUD CUSTOMERMEMBERSHIP -------#

def test_create_customer_membership(client, customer_with_credentials, membership):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    membership_id = membership["id"]

    response = client.post(
        f"/customers/assign-membership/{membership_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["customer_id"] == c["customer"]["id"]
    assert response.json()["membership_id"] == membership_id
    assert response.json()["status"] == MembershipStatusEnum.ACTIVE
    assert response.json()["start_date"] == date.today().isoformat()

def test_admins_cannot_create_customer_membership(client, admin_user, membership):
    token = login(client, admin_user["email"], admin_user["password"])

    membership_id = membership["id"]

    response = client.post(
        f"/customers/assign-membership/{membership_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_assign_same_membership_twice_returns_400(client, customer_with_credentials, membership):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    membership_id = membership["id"]

    response = client.post(
        f"/customers/assign-membership/{membership_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    response_2 = client.post(
        f"/customers/assign-membership/{membership_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    assert response_2.json()["detail"] == "El cliente ya posee esta membresía activa"

def test_reassign_membership_deactivates_previous(client, customer_with_membership, membership_2, session):
    c= customer_with_membership
    token = login(client, c["email"], c["password"])

    membership_id_2 = membership_2["id"]

    response = client.post(
        f"/customers/assign-membership/{membership_id_2}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED

    ultimo_dia, primer_dia_siguiente = obtener_ultimo_dia(date.today())

    previous_membership = session.exec(
        select(CustomerMembership)
        .where(CustomerMembership.customer_id == c["customer"]["id"])
        .order_by(CustomerMembership.id.asc())
    ).first()

    assert previous_membership.end_date == ultimo_dia
    assert response.json()["start_date"] == primer_dia_siguiente.isoformat()
    assert response.json()["status"] == MembershipStatusEnum.PENDING

def test_list_customer_membership_is_only_for_admin(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])  

    response = client.get("/customers/customer-memberships",
                          headers={"Authorization": f"Bearer {token}"})
    print(response.json())
    assert response.status_code == status.HTTP_200_OK

def test_get_active_membership_returns_active(client,admin_user,customer_with_membership):
    token = login(client, admin_user["email"], admin_user["password"])

    customer_id = customer_with_membership["customer"]["id"]
    response = client.get(
        f"/customers/{customer_id}/membership",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == MembershipStatusEnum.ACTIVE

def test_get_pending_membership_returns_pending(client,admin_user,customer_with_pending_membership):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.get(
        f"/customers/{customer_with_pending_membership['customer']['id']}/membership?status=pending",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == MembershipStatusEnum.PENDING


def test_read_customer_membership(client, customer_with_membership):
    c= customer_with_membership
    token = login(client, c["email"], c["password"])

    response = client.get("/customers/me/membership",
                          headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == status.HTTP_200_OK

def test_read_customer_membership_should_return_404(client, customer_with_membership):
    c= customer_with_membership
    token = login(client, c["email"], c["password"])

    response = client.get("/customers/me/membership?status=pending",
                          headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_list_customer_membership_paginated(
    client,
    admin_user,
    customer_with_membership
):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.get(
        "/customers/customer-memberships?page=1&size=1",
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