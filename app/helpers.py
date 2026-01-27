
def login(client, email, password) -> str:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def create_customer(client, **overrides):
    payload = {
        "first_name": "Pepe",
        "last_name": "Perez",
        "birth_date": "2000-12-12",
        "email": "default@example.com",
        "password": "password123",
    }
    payload.update(overrides)

    response = client.post("/customers/", json=payload)
    assert response.status_code == 201
    return response.json()