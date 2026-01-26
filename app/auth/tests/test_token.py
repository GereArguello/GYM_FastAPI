from fastapi import status
from datetime import timedelta
from sqlmodel import select
from app.auth.models import User
from app.core.security import create_access_token
from app.core.enums import RoleEnum

def test_token_allows_access_to_protected_endpoint(
    customer_with_credentials,
    client
):
    # login
    login_response = client.post(
        "/auth/login",
        data={
            "username": customer_with_credentials["email"],
            "password": customer_with_credentials["password"],
        }
    )

    token = login_response.json()["access_token"]


    # endpoint protegido
    response = client.get(
        "/customers/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == status.HTTP_200_OK

def test_should_return_401_if_token_is_missing(client):
    response = client.get("/customers/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_should_return_401_if_token_is_malformed(client):
    response = client.get(
        "/customers/me",
        headers={
            "Authorization": f"Bearer asd1234"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_should_return_401_if_user_is_not_active(client, user_is_not_active):
    login_response = client.post(
        "/auth/login",
        data={
            "username": user_is_not_active["email"],
            "password": user_is_not_active["password"],
        }
    )

    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED

def test_should_return_403_if_user_role_is_admin(client, user_role_is_admin):
    login_response = client.post(
        "/auth/login",
        data={
            "username": user_role_is_admin["email"],
            "password": user_role_is_admin["password"],
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/customers/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_should_return_401_if_token_expired(client, customer_with_credentials, session):
    customer_email = customer_with_credentials["email"]
    user = session.exec(select(User).where(User.email == customer_email)).first()

    token = create_access_token(
        data={"sub": str(user.id),"role": RoleEnum.CUSTOMER},
        expires_delta=timedelta(minutes=-1)
    )

    response = client.get(
        "/customers/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
