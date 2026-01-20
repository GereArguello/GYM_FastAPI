from fastapi import status
from app.memberships.models import Membership

def test_create_membership(client):
    response = client.post("/memberships/",json={
        "name" : "Premium",
        "max_days_per_week" : 5,
        "points_multiplier" : 1.5
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Premium"

def test_create_membership_fails_if_points_multiplier_is_less_than_one(client):
    response = client.post("/memberships/",json={
        "name" : "Premium",
        "max_days_per_week" : 5,
        "points_multiplier" : 0.9
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_read_membership(client):
    response = client.post("/memberships/",json={
        "name" : "Premium",
        "max_days_per_week" : 5,
        "points_multiplier" : 1.5
        }
    )
    assert response.status_code == status.HTTP_201_CREATED

    membership_id: int = response.json()["id"]
    response_read = client.get(f"/memberships/{membership_id}/")

    assert response_read.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Premium"

def test_read_membership_not_found(client):
    response = client.get("/memberships/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_membership(client):
    response = client.post("/memberships/",json={
        "name" : "Premium",
        "max_days_per_week" : 5,
        "points_multiplier" : 1.5
        }
    )

    membership_id: int = response.json()["id"]
    response_update = client.patch(f"/memberships/{membership_id}",json={
        "max_days_per_week": 4
    })

    updated_membership = response_update.json()

    assert updated_membership["max_days_per_week"] == 4

    assert updated_membership["name"] == response.json()["name"]

def test_delete_membership(client, session):
    response = client.post("/memberships/",json={
        "name" : "Premium",
        "max_days_per_week" : 5,
        "points_multiplier" : 1.5
        }
    )
    membership_id: int = response.json()["id"]

    response_delete = client.delete(f"/memberships/{membership_id}")
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT

    deleted_membership = session.get(Membership, membership_id)
    assert deleted_membership is None