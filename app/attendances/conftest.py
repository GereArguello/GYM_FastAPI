import pytest
from fastapi import status
from app.helpers import login

@pytest.fixture(name="attendance")
def attendance(client, customer_with_membership):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    response = client.post("/attendances/",
                           headers={"Authorization": f"Bearer {token}"},
                           json={})

    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

@pytest.fixture(name="checkout_attendance")
def checkout_attendance(client,customer_with_membership, attendance):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    attendance_id = attendance["id"]
    response = client.patch(f"/attendances/{attendance_id}/checkout/",
                            headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    return attendance_id