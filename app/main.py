from fastapi import FastAPI
from app.customers import routes as customers_router


app = FastAPI()

app.include_router(customers_router.router)

@app.get("/")
async def root():
    return {"Mensaje": "Bienvenido"}