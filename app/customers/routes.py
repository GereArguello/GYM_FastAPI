from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from datetime import date
from app.core.database import SessionDep
from app.core.enums import StatusEnum
from app.customers.models import Customer, CustomerMembership
from app.customers.schemas import CustomerCreate, CustomerRead, CustomerUpdate, CustomerMembershipRead
from app.memberships.models import Membership
from app.customers.services import register_customer
from app.auth.dependencies import get_current_customer

router = APIRouter(
    prefix="/customers",
    tags=["customers"]
)


@router.post("/",
            response_model=CustomerRead,
            status_code=status.HTTP_201_CREATED
)
def register_customer_endpoint(customer_data: CustomerCreate,session: SessionDep):
    try:
        customer = register_customer(session, customer_data)
        return customer

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está siendo utilizado"
        )
    
@router.get("/me", response_model=CustomerRead)
def read_me(current_customer: Customer = Depends(get_current_customer)):

    return current_customer


@router.get("/", response_model=list[CustomerRead])
def list_customers(
    session: SessionDep,
    include_inactive: bool = False, 
    search: str | None = None
):
    
    query = select(Customer)

    #--- A futuro los no activos solo serán visibles para el staff ---#
    
    if not include_inactive:
        query = query.where(Customer.is_active == StatusEnum.ACTIVE)

    if search:
            query = query.where(
        (Customer.first_name.ilike(f"%{search}%")) |
        (Customer.last_name.ilike(f"%{search}%"))
    )
    
    return session.exec(query).all()

@router.get("/{customer_id}", response_model=CustomerRead)
def read_customer(customer_id: int, session: SessionDep):    
    customer = session.get(Customer, customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cliente no encontrado")
    return customer


@router.patch("/{customer_id}", response_model=CustomerRead, status_code=status.HTTP_200_OK)
def update_customer(customer_id: int, customer_data: CustomerUpdate, session: SessionDep):
    customer = session.get(Customer, customer_id)

    if not customer or not customer.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Cliente no encontrado")
    
    update_data = customer_data.model_dump(exclude_unset=True)

    customer.sqlmodel_update(update_data)
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

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, session: SessionDep):
    customer = session.get(Customer, customer_id)

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Cliente no encontrado")
    
    session.delete(customer)
    session.commit()

@router.post("/{customer_id}/membership/{membership_id}",
             response_model=CustomerMembershipRead,
             status_code=status.HTTP_201_CREATED)
def assign_membership(
    customer_id: int,
    membership_id: int,
    session: SessionDep
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer no encontrado")

    membership = session.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership no encontrada")

    # Desactivar membership activa previa (si existe)
    active_membership = session.exec(
        select(CustomerMembership)
        .where(
            CustomerMembership.customer_id == customer_id,
            CustomerMembership.is_active == True
        )
    ).first()

    # Verificar que no se asigne la misma membresía
    if active_membership and active_membership.membership_id == membership_id:
        raise HTTPException(
            status_code=400,
            detail="El cliente ya posee esta membresía activa"
        )

    # Desactivar membresía actual
    if active_membership:
        active_membership.is_active = False
        active_membership.end_date = date.today()

    # Crear nueva membresía
    customer_membership = CustomerMembership(
        customer_id=customer_id,
        membership_id=membership_id
    )

    session.add(customer_membership)
    session.commit()
    session.refresh(customer_membership)

    return customer_membership

@router.get("/memberships", response_model=list[CustomerMembershipRead])
def list_customer_memberships(
    session: SessionDep,
    include_inactive: bool=False 
):
    query = select(CustomerMembership)

    if not include_inactive:
        query = query.where(CustomerMembership.is_active == True)
    
    return session.exec(query).all()

@router.get("/{customer_id}/membership/active", response_model=CustomerMembershipRead)
def get_active_membership(
    customer_id: int,
    session: SessionDep
):
    # Validar customer
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer no encontrado")

    active_membership = session.exec(
        select(CustomerMembership)
        .where(
            CustomerMembership.customer_id == customer_id,
            CustomerMembership.is_active == True
        )
    ).first()

    if not active_membership:
        raise HTTPException(
            status_code=404,
            detail="El customer no posee una membresía activa"
        )

    return active_membership
