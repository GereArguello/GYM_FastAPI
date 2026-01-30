
def login(client, email, password) -> str:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def create_customer(client, **overrides):
    """
    Helper de testing para crear un cliente vía la API.

    Se utiliza en tests para evitar repetir el payload de creación
    de clientes. Permite sobrescribir campos específicos mediante
    argumentos keyword.

    Nota:
    - No debe utilizarse fuera del entorno de tests.
    """
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