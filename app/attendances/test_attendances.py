from fastapi import status
from freezegun import freeze_time
from datetime import datetime, timezone, timedelta
from app.attendances.models import Attendance
from app.helpers import login


def test_create_attendance(client, customer_with_membership):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    response = client.post("/attendances/",
                           headers={"Authorization": f"Bearer {token}"},
                           json={})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["check_in"] is not None

def test_create_attendance_fails_if_customer_has_no_membership(client, customer_with_credentials):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    response = client.post("/attendances/",
                           headers={"Authorization": f"Bearer {token}"},
                           json={})

    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_should_fail_if_cuistomer_has_already_an_assistance_today(client, customer_with_membership, attendance):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    response = client.post("/attendances/",
                           headers={"Authorization": f"Bearer {token}"},
                           json={})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Ya tenés una asistencia activa"

@freeze_time("2026-01-10 15:30:00")
def test_create_attendance_fails_if_customer_has_reached_weekly_limit(
    client,
    customer_with_membership,
    session
):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    #Ocurren del lunes al viernes
    base_monday = datetime(2026, 1, 5, 15, 30, tzinfo=timezone.utc)  # lunes

    # Creamos el máximo permitido de asistencias
    for day_offset in range(5):
        response = client.post(
            "/attendances/",
            headers={"Authorization" : f"Bearer {token}"},
            json={}
        )
        assert response.status_code == status.HTTP_201_CREATED

        attendance = session.get(Attendance, response.json()["id"])
        attendance.check_in = base_monday + timedelta(days=day_offset)
        session.add(attendance)

    session.commit()

    # Intentamos crear una más (debe fallar) esta ocurre SABADO
    response = client.post(
        "/attendances/",
        headers={"Authorization" : f"Bearer {token}"},
        json={}
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Límite semanal de asistencias alcanzado"


def test_checkout_attendance_not_found(client, customer_with_membership):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    response = client.patch("/attendances/999/checkout/",
                            headers={"Authorization" : f"Bearer {token}"})

    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_checkout_fails_if_attendance_is_already_checked_out(client,customer_with_membership, checkout_attendance):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])
    response = client.patch(f"/attendances/{checkout_attendance}/checkout/",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Asistencia ya finalizada"

def test_checkout_fails_if_attendance_is_from_previous_day(client, session, customer_with_membership, attendance):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    attendance_id = attendance["id"]
    db_attendance = session.get(Attendance, attendance_id)

    db_attendance.check_in = datetime.now(timezone.utc) - timedelta(days=1)
    session.commit()
    response = client.patch(f"/attendances/{attendance_id}/checkout/",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "No se puede finalizar una asistencia de un día anterior"



def test_checkout_attendance_is_valid_if_duration_is_at_least_30_minutes(
    client,
    session,
    attendance,
    customer_with_membership
):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    attendance_id = attendance["id"]

    #Manipulamos el estado previo
    db_attendance = session.get(Attendance, attendance_id)
    db_attendance.check_in = datetime.now(timezone.utc) - timedelta(minutes=35)
    session.commit()

    response = client.patch(f"/attendances/{attendance_id}/checkout/",
                            headers={"Authorization" : f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_valid"] is True
    assert data["duration_minutes"] >= 30
    assert data["points_awarded"] == 15

def test_checkout_attendance_is_invalid_if_duration_is_less_than_30_minutes(
    client,
    session,
    attendance,
    customer_with_membership
):
    c = customer_with_membership
    token = login(client, c["email"], c["password"])

    attendance_id = attendance["id"]

    db_attendance = session.get(Attendance, attendance_id)
    db_attendance.check_in = datetime.now(timezone.utc) - timedelta(minutes=10)
    session.commit()

    response = client.patch(f"/attendances/{attendance_id}/checkout/",
                            headers={"Authorization" : f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["is_valid"] is False
    assert data["duration_minutes"] < 30
    assert data["points_awarded"] == 0

def test_read_attendance(client, attendance, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])
    attendance_id = attendance["id"]

    response = client.get(f"/attendances/{attendance_id}/",
                          headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK

def test_read_attendance_not_found(client, admin_user):
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.get("/attendances/999/",
                        headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_404_NOT_FOUND