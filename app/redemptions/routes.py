from fastapi import APIRouter, status, HTTPException
from sqlmodel import select
from app.redemptions.models import Redemption
from app.redemptions.schemas import RedemptionRead, RedemptionCreate
from app.shop.models import Product
from app.customers.models import Customer
from app.core.database import SessionDep
from app.core.enums import ProductType


router = APIRouter(prefix="/redemptions",
                   tags=["redemptions"])

@router.post("/{customer_id}",response_model=RedemptionRead, status_code=status.HTTP_201_CREATED)
def create_redemption(data: RedemptionCreate, customer_id: int, session: SessionDep):
    
    product = session.get(Product, data.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Producto no encontrado")
    
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Customer no encontrado")
    
    if not product.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Producto no disponible")
    
    if product.product_type != ProductType.POINTS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Este producto no es canjeable por puntos")

    if product.stock < data.quantity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No hay stock suficiente")
    
    customer_points = customer.points_balance
    redemption_cost = product.price * data.quantity

    if customer_points < redemption_cost:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No tienes puntos suficientes")
    
    customer.points_balance -= redemption_cost
    product.stock -= data.quantity

    redemption = (Redemption(customer_id=customer_id,
                             product_id=data.product_id,
                             points_spent=redemption_cost,
                             quantity=data.quantity,
                             product_name_snapshot=product.name))
    session.add(redemption)
    session.commit()
    session.refresh(redemption)

    return redemption

@router.get("/", response_model=list[RedemptionRead], status_code=status.HTTP_200_OK)
def list_redemptions(session: SessionDep):
    return session.exec(select(Redemption)).all()

@router.get("/{redemption_id}", response_model=RedemptionRead, status_code=status.HTTP_200_OK)
def read_redemption(redemption_id: int, session: SessionDep):
    redemption = session.get(Redemption, redemption_id)

    if not redemption:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail="canje no encontrado")
    
    return redemption
    
    
    

