from fastapi import status
from app.memberships.models import Membership
from app.helpers import login

def test_create_membership(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.post("/memberships/",
        headers={"Authorization": f"Bearer {token}"},
        json={
        "name" : "Premium",
        "max_days_per_week" : 5,
        "points_multiplier" : 1.5
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Premium"

def test_create_membership_fail_if_are_created_by_customer(client, customer_with_credentials):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    response = client.post("/memberships/",
        headers={"Authorization": f"Bearer {token}"},
        json={
        "name" : "Premium",
        "max_days_per_week" : 5,
        "points_multiplier" : 1.5
        }
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_create_membership_fails_if_points_multiplier_is_less_than_one(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    response = client.post(
        "/memberships/",
        headers={"Authorization": f"Bearer {token}"},
        json={
        "name" : "Premium",
        "max_days_per_week" : 5,
        "points_multiplier" : 0.9
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_admin_can_list_inactive_memberships(client, admin_user, membership_inactive):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.get(
        "/memberships/?include_inactive=true",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["is_active"] is False

def test_read_list_membership_should_return_empty(client, membership_inactive):
    response = client.get("/memberships/?include_inactive=true")
    assert response.json() == []

def test_read_membership(client, membership):
    membership_id = membership["id"]

    response = client.get(f"/memberships/{membership_id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Premium"


def test_read_membership_not_found(client):
    response = client.get("/memberships/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_membership(client, admin_user, membership):
    token = login(client, admin_user["email"], admin_user["password"])

    membership_id = membership["id"]

    response = client.patch(f"/memberships/{membership_id}",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "max_days_per_week": 4
    })
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["max_days_per_week"] == 4
    assert response.json()["name"] == membership["name"]

def test_customer_cannot_update_membership(client, customer_with_credentials, membership):
    token = login(client, customer_with_credentials["email"], customer_with_credentials["password"])
    response = client.patch(
        f"/memberships/{membership['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"max_days_per_week": 3}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN



def test_delete_membership(client, session, admin_user, membership):
    token = login(client, admin_user["email"], admin_user["password"])
    membership_id = membership["id"]

    response_delete = client.delete(f"/memberships/{membership_id}/deactivate",
                                    headers={"Authorization": f"Bearer {token}"})
    
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT

    deleted_membership = session.get(Membership, membership_id)
    assert deleted_membership.is_active == False