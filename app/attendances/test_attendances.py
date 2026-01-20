from fastapi import status
from datetime import datetime, timezone, timedelta
from app.attendances.models import Attendance


def test_create_attendance(client, customer_with_membership):
    customer_id = customer_with_membership["id"]

    response = client.post("/attendances/", json={
        "customer_id": customer_id
    })

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["check_in"] is not None

def test_create_attendance_fails_if_customer_has_no_membership(client, customer):
    customer_id = customer["id"]

    response = client.post("/attendances/", json={
        "customer_id": customer_id
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_create_attendance_fails_if_customer_has_reached_weekly_limit(
    client,
    session,
    customer_with_membership
):
    customer_id = customer_with_membership["id"]

    # Creamos el máximo permitido de asistencias
    for _ in range(5):
        response = client.post(
            "/attendances/",
            json={"customer_id": customer_id}
        )
        assert response.status_code == status.HTTP_201_CREATED

    # Intentamos crear una más (debe fallar)
    response = client.post(
        "/attendances/",
        json={"customer_id": customer_id}
    )

    assert response.status_code == status.HTTP_409_CONFLICT

def test_checkout_attendance_not_found(client):
    response = client.patch("/attendances/999/checkout/")

    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_checkout_fails_if_attendance_is_already_checked_out(client, checkout_attendance):
    response = client.patch(f"/attendances/{checkout_attendance}/checkout/")

    assert response.status_code == status.HTTP_409_CONFLICT

def test_checkout_attendance_is_valid_if_duration_is_at_least_30_minutes(
    client,
    session,
    attendance
):
    attendance_id = attendance["id"]

    #Manipulamos el estado previo
    db_attendance = session.get(Attendance, attendance_id)
    db_attendance.check_in = datetime.now(timezone.utc) - timedelta(minutes=35)
    session.commit()

    response = client.patch(f"/attendances/{attendance_id}/checkout")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_valid"] is True
    assert data["duration_minutes"] >= 30
    assert data["points_awarded"] == 15

def test_checkout_attendance_is_invalid_if_duration_is_less_than_30_minutes(
    client,
    session,
    attendance
):
    attendance_id = attendance["id"]

    db_attendance = session.get(Attendance, attendance_id)
    db_attendance.check_in = datetime.now(timezone.utc) - timedelta(minutes=10)
    session.commit()

    response = client.patch(f"/attendances/{attendance_id}/checkout/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["is_valid"] is False
    assert data["duration_minutes"] < 30
    assert data["points_awarded"] == 0

def test_read_attendance(client, attendance):
    attendance_id = attendance["id"]

    response = client.get(f"/attendances/{attendance_id}/")

    assert response.status_code == status.HTTP_200_OK

def test_read_attendance_not_found(client):

    response = client.get("/attendances/999/")

    assert response.status_code == status.HTTP_404_NOT_FOUND