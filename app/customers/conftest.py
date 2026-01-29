from fastapi import status
import pytest
from sqlmodel import select
from app.core.enums import MembershipStatusEnum
from app.customers.models import CustomerMembership
from app.helpers import login


@pytest.fixture(name="membership")
def membership(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    response = client.post(
        "/memberships/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Premium",
            "max_days_per_week": 5,
            "points_multiplier": 1.5
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

@pytest.fixture(name="membership_2")
def membership_2(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    response = client.post(
        "/memberships/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "medium",
            "max_days_per_week": 3,
            "points_multiplier": 1.2
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


@pytest.fixture(name="customer_with_pending_membership")
def customer_with_pending_membership(
    client,
    customer_with_credentials,
    membership,
    membership_2,
    session
):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    # crear activa
    response = client.post(
        f"/customers/assign-membership/{membership['id']}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    # crear segunda → queda PENDING
    response = client.post(
        f"/customers/assign-membership/{membership_2['id']}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    pending_membership = session.exec(
        select(CustomerMembership)
        .where(
            CustomerMembership.customer_id == c["customer"]["id"],
            CustomerMembership.status == MembershipStatusEnum.PENDING
        )
    ).first()

    return {
        "customer": c["customer"],
        "membership": pending_membership
    }




        
