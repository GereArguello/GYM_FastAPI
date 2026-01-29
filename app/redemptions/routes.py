from fastapi import APIRouter, status, HTTPException, Depends
from sqlmodel import select
from app.redemptions.models import Redemption
from app.redemptions.schemas import RedemptionRead, RedemptionCreate
from app.shop.models import Product
from app.customers.models import Customer
from app.core.database import SessionDep
from app.core.enums import ProductType, RoleEnum
from app.auth.dependencies import get_current_customer, check_admin, get_current_user
from app.auth.models import User


router = APIRouter(prefix="/redemptions",
                   tags=["redemptions"])

@router.post("/",response_model=RedemptionRead, status_code=status.HTTP_201_CREATED)
def create_redemption(data: RedemptionCreate,
                      session: SessionDep,
                      current_customer: Customer = Depends(get_current_customer)):
    
    product = session.get(Product, data.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Producto no encontrado")
    
    if not product.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Producto no disponible")
    
    if product.product_type != ProductType.POINTS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Este producto no es canjeable por puntos")

    if data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad debe ser mayor a cero"
        )

    if product.stock < data.quantity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No hay stock suficiente")

    
    customer_points = current_customer.points_balance
    redemption_cost = product.price * data.quantity

    if customer_points < redemption_cost:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No tienes puntos suficientes")
    

    current_customer.points_balance -= redemption_cost
    product.stock -= data.quantity

    redemption = (Redemption(customer_id=current_customer.id,
                            product_id=data.product_id,
                            points_spent=redemption_cost,
                            quantity=data.quantity,
                            product_name_snapshot=product.name))
    session.add(redemption)
    session.commit()
    session.refresh(redemption)

    return redemption

@router.get("/", response_model=list[RedemptionRead], status_code=status.HTTP_200_OK)
def list_redemptions(session: SessionDep, admin: User = Depends(check_admin)):
    return session.exec(select(Redemption)).all()

@router.get("/me", response_model=list[RedemptionRead])
def list_my_redemptions(
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer)
):
    return session.exec(
        select(Redemption).where(Redemption.customer_id == current_customer.id)
    ).all()

@router.get("/{redemption_id}", response_model=RedemptionRead)
def read_redemption(
    redemption_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    redemption = session.get(Redemption, redemption_id)
    if not redemption:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canje no encontrado"
        )

    if current_user.role == RoleEnum.ADMIN:
        return redemption

    customer = session.exec(
        select(Customer).where(Customer.user_id == current_user.id)
    ).first()

    if not customer or redemption.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canje no encontrado"
        )

    return redemption

    
    
