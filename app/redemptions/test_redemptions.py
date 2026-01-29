from fastapi import status
from app.helpers import login

def test_should_fail_if_product_not_found(client,customer_with_credentials):
    c = customer_with_credentials

    token = login(client, c["email"], c["password"])

    response = client.post(
        "/redemptions/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": 999,
            "quantity": 1
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Producto no encontrado"

def test_should_fail_if_product_is_not_active(
    client,
    customer_with_credentials,
    customer_with_75_points,
    product_is_not_active
):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    r = client.post(
        f"/redemptions/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product_is_not_active.id,
            "quantity": 1
        }
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["detail"] == "Producto no disponible"

def test_should_fail_if_product_is_with_money(
        client,
        customer_with_credentials,
        customer_with_75_points,
        product_with_money
):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])   


    r = client.post(
        f"/redemptions/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product_with_money.id,
            "quantity": 1
        }
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["detail"] == "Este producto no es canjeable por puntos"

def test_should_fail_if_product_stock_is_not_enought(
        client,
        customer_with_credentials,
        customer_with_75_points,
        product_without_stock
):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])   

    r = client.post(
        f"/redemptions/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product_without_stock.id,
            "quantity": 1
        }
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["detail"] == "No hay stock suficiente"

def test_should_fail_if_customer_points_is_not_enough(
        client,
        customer_with_credentials,
        customer_with_75_points,
        expensive_product
):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])  

    r = client.post(
        f"/redemptions/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": expensive_product.id,
            "quantity": 1
        }
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["detail"] == "No tienes puntos suficientes"

def test_create_redemption(
        client,
        session,
        customer_with_credentials,
        customer_with_75_points,
        cheap_product
):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    r = client.post(
        f"/redemptions/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": cheap_product.id,
            "quantity": 1
        }
    )

    assert r.status_code == status.HTTP_201_CREATED

    session.refresh(customer_with_75_points)
    session.refresh(cheap_product)

    assert customer_with_75_points.points_balance == 5
    assert cheap_product.stock == 4

def test_list_redemptions(client,
                          redemption,
                          admin_user):
    
    token = login(client, admin_user["email"], admin_user["password"])

    response = client.get("/redemptions/",
                          headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK

def test_list_redemptions_should_fail_for_customer(client,
                          redemption,
                          customer_with_credentials):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    response = client.get("/redemptions/",
                          headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_read_redemption(client, customer_with_credentials, redemption, cheap_product):
    c = customer_with_credentials
    token = login(client, c["email"], c["password"])

    customer_id = c["customer"]["id"]

    redemption_id = redemption["id"]

    response = client.get(f"/redemptions/{redemption_id}",
                           headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["customer_id"] == customer_id
    assert response.json()["points_spent"] == cheap_product.price
    assert "created_at" in response.json()
    


    