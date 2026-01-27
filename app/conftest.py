import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session
from app.main import app
from app.core.database import get_session
from app.core.security import get_password_hash
from app.core.enums import RoleEnum
from app.auth.models import User



sqlite_url = "sqlite://"

engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="admin_user")
def admin_user(session):
    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role=RoleEnum.ADMIN,
        is_active=True
    )

    session.add(admin)
    session.commit()
    session.refresh(admin)

    return {
        "email": admin.email,
        "password": "admin123"
    }


@pytest.fixture(name="customer_with_credentials")
def customer_with_credentials(client):
    payload = {
        "first_name": "Pepe",
        "last_name": "Perez",
        "birth_date": "2000-12-12",
        "email": "example@example.com",
        "password": "password123"
    }

    response = client.post("/customers/", json=payload)
    assert response.status_code == 201

    return {
        "customer": response.json(),
        "email": payload["email"],
        "password": payload["password"],
    }
