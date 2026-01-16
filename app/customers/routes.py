from fastapi import APIRouter, status, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from core.database import SessionDep
from customers.models import Customer
from customers.schemas import CustomerCreate, CustomerRead, CustomerUpdate

router = APIRouter(tags=["customers"])


@router.post("/customers",
            response_model=CustomerRead,
            status_code=status.HTTP_201_CREATED
)
def create_customer(customer_data: CustomerCreate,session: SessionDep):
    customer = Customer(**customer_data.model_dump())

    try:
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está siendo utilizado"
        )

@router.get("/customers", response_model=list[CustomerRead])
def list_customers(
    session: SessionDep,
    include_inactive: bool = False, 
    search: str | None = None
):
    
    query = select(Customer)

    #--- A futuro los no activos solo serán visibles para el staff ---#
    
    if not include_inactive:
        query = query.where(Customer.is_active == True)

    if search:
        query = query.where(Customer.name.ilike(f"%{search}%"))
    
    return session.exec(query).all()

@router.get("/customers/{customer_id}", response_model=CustomerRead)
def read_customer(customer_id: int, session: SessionDep):    
    customer = session.get(Customer, customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cliente no encontrado")
    return customer

@router.patch("/customers/{customer_id}", response_model=CustomerRead, status_code=status.HTTP_200_OK)
def update_customer(customer_id: int, customer_data: CustomerUpdate, session: SessionDep):
    customer = session.get(Customer, customer_id)

    if not customer or not customer.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Cliente no encontrado")
    
    data = customer_data.model_dump(exclude_unset=True)

    customer.sqlmodel_update(data)
    try:
        session.commit()
        session.refresh(customer)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está siendo utilizado"
        )

    return customer

@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, session: SessionDep):
    customer = session.get(Customer, customer_id)

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Cliente no encontrado")
    
    session.delete(customer)
    session.commit()
    return {"detail": "ok"}

