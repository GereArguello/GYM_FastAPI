import pytest
from sqlmodel import select
from app.auth.models import User
from app.core.enums import RoleEnum


@pytest.fixture(name="user_is_not_active")
def user_is_not_active(client, session):
    payload = {
        "first_name": "Pepe",
        "last_name": "Perez",
        "birth_date": "2000-12-12",
        "email": "example@example.com",
        "password": "password123"
    }

    response = client.post("/customers/", json=payload)
    assert response.status_code == 201

    email = payload["email"]
    user = session.exec(select(User).where(User.email == email)).first()
    user.is_active = False
    session.commit()

    assert user is not None

    return {
        "customer": response.json(),
        "email": payload["email"],
        "password": payload["password"],
    }

@pytest.fixture(name="user_role_is_admin")
def user_role_is_admin(client, session):
    payload = {
        "first_name": "Pepe",
        "last_name": "Perez",
        "birth_date": "2000-12-12",
        "email": "example@example.com",
        "password": "password123"
    }

    response = client.post("/customers/", json=payload)
    assert response.status_code == 201

    email = payload["email"]
    user = session.exec(select(User).where(User.email == email)).first()
    user.role = RoleEnum.ADMIN
    session.commit()

    assert user is not None

    return {
        "customer": response.json(),
        "email": payload["email"],
        "password": payload["password"],
    }