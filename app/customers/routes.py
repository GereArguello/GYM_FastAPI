from fastapi import APIRouter, status, HTTPException, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from sqlalchemy.exc import IntegrityError
from sqlmodel import select, desc
from datetime import date
from app.core.database import SessionDep
from app.core.enums import StatusEnum, MembershipStatusEnum
from app.core.pagination import DefaultPagination
from app.customers.models import Customer, CustomerMembership
from app.customers.schemas import CustomerCreate, CustomerRead, CustomerUpdate, CustomerMembershipRead
from app.memberships.models import Membership
from app.customers.services import register_customer, obtener_ultimo_dia
from app.auth.dependencies import get_current_customer, check_admin
from app.auth.models import User

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


@router.get("/", response_model=Page[CustomerRead])
def list_customers(
    session: SessionDep,
    include_inactive: bool = False, 
    search: str | None = None,
    admin: User = Depends(check_admin),
    params: DefaultPagination = Depends()
):
    
    query = select(Customer)

    if not include_inactive:
        query = query.where(Customer.is_active == StatusEnum.ACTIVE)

    if search:
            query = query.where(
        (Customer.first_name.ilike(f"%{search}%")) |
        (Customer.last_name.ilike(f"%{search}%"))
    )
    query = query.order_by(Customer.last_name, Customer.first_name)

    
    return paginate(session,query,params)


@router.patch("/me", response_model=CustomerRead, status_code=status.HTTP_200_OK)
def update_customer(customer_data: CustomerUpdate,
                    session: SessionDep,
                    current_customer: Customer = Depends(get_current_customer)):

    update_data = customer_data.model_dump(exclude_unset=True)

    current_customer.sqlmodel_update(update_data)

    session.commit()
    session.refresh(current_customer)

    return current_customer

@router.delete("/me/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_customer_me(session: SessionDep,
                    current_customer: Customer = Depends(get_current_customer)):
    current_customer.is_active = StatusEnum.INACTIVE
    session.commit()

#---------ENDPOINTS PARA RELACIONAR CUSTOMERS Y MEMBERSHIPS----------#


@router.post("/assign-membership/{membership_id}",
             response_model=CustomerMembershipRead,
             status_code=status.HTTP_201_CREATED)
def assign_membership(
    membership_id: int,
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer)
):
    customer_id = current_customer.id

    membership = session.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership no encontrada")


    # Encontrar membresía activa
    active_membership = session.exec(
        select(CustomerMembership)
        .where(
            CustomerMembership.customer_id == customer_id,
            CustomerMembership.status == MembershipStatusEnum.ACTIVE
        )
    ).first()

    # Verificar que no se asigne la misma membresía
    if active_membership and active_membership.membership_id == membership_id:
        raise HTTPException(
            status_code=400,
            detail="El cliente ya posee esta membresía activa"
        )
    
    ultimo_dia, primer_dia_siguiente = obtener_ultimo_dia(date.today())

    # Programar fin de membresía
    if active_membership:
        active_membership.end_date = ultimo_dia

        # Programar comienzo de membresía
        customer_membership = CustomerMembership(
            customer_id=customer_id,
            membership_id=membership_id,
            start_date=primer_dia_siguiente,
            status=MembershipStatusEnum.PENDING
        )

    else:
        customer_membership = CustomerMembership(
            customer_id=customer_id,
            membership_id=membership_id,
            start_date=date.today(),
            end_date=primer_dia_siguiente,
            status=MembershipStatusEnum.ACTIVE
        )
    try:
        session.add(customer_membership)
        session.commit()
        session.refresh(customer_membership)
    except Exception:
        session.rollback()
        raise

    return customer_membership



@router.get("/customer-memberships", response_model=Page[CustomerMembershipRead])
def list_customer_memberships(
    session: SessionDep,
    include_inactive: bool=False,
    admin: User = Depends(check_admin),
    params: DefaultPagination = Depends()
):
    query = select(CustomerMembership)

    if not include_inactive:
        query = query.where(CustomerMembership.status == MembershipStatusEnum.ACTIVE)
    
    query = query.order_by(desc(CustomerMembership.id))
    return paginate(session,query,params)

@router.get("/me/membership", response_model=CustomerMembershipRead)
def read_my_membership(session: SessionDep, 
                       current_customer: Customer = Depends(get_current_customer),
                       status: MembershipStatusEnum = MembershipStatusEnum.ACTIVE):
    
    membership = session.exec(select(CustomerMembership)
                         .where(CustomerMembership.customer_id == current_customer.id,
                                CustomerMembership.status == status)).first()
    if not membership:
        raise HTTPException(404,f"El customer no posee una membresía {status.value}")
    
    return membership

@router.get("/{customer_id}/membership",response_model=CustomerMembershipRead)
def get_customer_membership(
    customer_id: int,
    session: SessionDep,
    status: MembershipStatusEnum = MembershipStatusEnum.ACTIVE,
    admin: User = Depends(check_admin)
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer no encontrado")

    membership = session.exec(
        select(CustomerMembership)
        .where(
            CustomerMembership.customer_id == customer_id,
            CustomerMembership.status == status
        )
    ).first()

    if not membership:
        raise HTTPException(404,f"El customer no posee una membresía {status.value}")

    return membership


#rutas dinámicas van despúes
@router.get("/{customer_id}", response_model=CustomerRead)
def read_customer(customer_id: int,
                  session: SessionDep,
                  admin: User = Depends(check_admin)
):    
    customer = session.get(Customer, customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cliente no encontrado")
    return customer

    

