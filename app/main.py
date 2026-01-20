from fastapi import FastAPI
from app.customers import routes as customers_router
from app.memberships import routes as memberships_router
from app.attendances import routes as attendances_router
from app.shop import routes as shop_router

app = FastAPI()

app.include_router(customers_router.router)
app.include_router(memberships_router.router)
app.include_router(attendances_router.router)
app.include_router(shop_router.router)

@app.get("/")
async def root():
    return {"Mensaje": "Bienvenido"}