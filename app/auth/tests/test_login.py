from fastapi import status

def test_customer_can_login(customer_with_credentials, client):
    response = client.post(
        "/auth/login",
        data={
            "username": customer_with_credentials["email"],
            "password": customer_with_credentials["password"],
        }
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

def test_login_should_fail_if_credentials_are_invalid(customer_with_credentials, client):
    response = client.post(
        "/auth/login",
        data={
            "username": customer_with_credentials["email"],
            "password": "wrong password"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Usuario o contraseña incorrectos"

def test_login_should_fail_if_payload_is_invalid(client):
    response = client.post(
        "/auth/login",
        data={
            "password": "wrong password"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT