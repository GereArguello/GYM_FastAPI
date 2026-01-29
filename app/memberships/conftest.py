import pytest


@pytest.fixture(name="membership_inactive")
def membership_inactive(client, admin_user):
    login = client.post(
        "/auth/login",
        data={
            "username": admin_user["email"],
            "password": admin_user["password"],
        }
    )
    token = login.json()["access_token"]

    response = client.post(
        "/memberships/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Premium",
            "max_days_per_week": 5,
            "points_multiplier": 1.5,
        }
    )
    membership = response.json()

    # desactivar
    client.delete(
        f"/memberships/{membership['id']}/deactivate",
        headers={"Authorization": f"Bearer {token}"}
    )

    return membership