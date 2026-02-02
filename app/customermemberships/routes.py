from fastapi import APIRouter, status, HTTPException, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from sqlmodel import select, desc
from datetime import date
from app.core.database import SessionDep
from app.core.enums import MembershipStatusEnum
from app.core.pagination import DefaultPagination
from app.customers.models import Customer
from app.customermemberships.models import CustomerMembership
from app.customermemberships.schemas import CustomerMembershipRead
from app.memberships.models import Membership
from app.customers.services import obtener_ultimo_dia
from app.auth.dependencies import get_current_customer, check_admin
from app.auth.models import User

router = APIRouter(
    prefix="/customer-memberships",
    tags=["customer-memberships"]
)


@router.post(
    "/assign/{membership_id}",
    response_model=CustomerMembershipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar una membresía al cliente",
    description="""
    Asigna una membresía al cliente autenticado.

    Comportamiento:
    - Si el cliente no tiene una membresía activa, la nueva se activa inmediatamente.
    - Si el cliente ya tiene una membresía activa, esta se programa para comenzar
      cuando finalice la actual (estado PENDING).
    - No se permite asignar la misma membresía si ya está activa.
    - La membresía activa siempre finaliza al último día del mes.

    Reglas:
    - Solo puede existir una membresía activa por cliente.
    - El cliente solo puede asignarse membresías a sí mismo.
    """,
    responses={
        201: {"description": "Membresía asignada correctamente"},
        400: {"description": "El cliente ya posee esta membresía activa"},
        404: {"description": "Membresía no encontrada"},
        401: {"description": "No autenticado"},
        403: {"description": "Token inválido o sin permisos"},
    },
)
def assign_membership(
    membership_id: int,
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
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

    if active_membership:
        active_membership.end_date = ultimo_dia

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


@router.get(
    "/",
    response_model=Page[CustomerMembershipRead],
    status_code=status.HTTP_200_OK,
    summary="Listar membresías de clientes",
    description="""
    Devuelve una lista paginada de las membresías asignadas a los clientes.

    - Solo accesible por administradores.
    - Por defecto solo muestra membresías activas.
    - Permite incluir membresías inactivas mediante el parámetro `include_inactive`.
    - Los resultados se ordenan por fecha de creación (más recientes primero).
    """,
    responses={
        200: {"description": "Lista de membresías obtenida correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo administradores)"},
    },
)
def list_customer_memberships(
    session: SessionDep,
    include_inactive: bool = False,
    admin: User = Depends(check_admin),
    params: DefaultPagination = Depends(),
):
    query = select(CustomerMembership)

    if not include_inactive:
        query = query.where(CustomerMembership.status == MembershipStatusEnum.ACTIVE)

    query = query.order_by(desc(CustomerMembership.id))

    return paginate(session, query, params)

# TODO: ordenar por end_date cuando status=INACTIVE (histórico de membresías)
@router.get(
    "/me",
    response_model=CustomerMembershipRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener mi membresía",
    description="""
    Devuelve la membresía del cliente autenticado según el estado solicitado.

    - Por defecto devuelve la membresía activa.
    - Permite consultar membresías pendientes o inactivas usando el parámetro `status`.
    - Solo devuelve membresías del propio cliente.
    - Requiere autenticación con token Bearer.
    """,
    responses={
        200: {"description": "Membresía obtenida correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Token inválido o sin permisos"},
        404: {"description": "El cliente no posee una membresía con el estado solicitado"},
    },
)
def read_my_membership(
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
    status: MembershipStatusEnum = MembershipStatusEnum.ACTIVE,
):
    membership = session.exec(
        select(CustomerMembership)
        .where(
            CustomerMembership.customer_id == current_customer.id,
            CustomerMembership.status == status
        )
    ).first()

    if not membership:
        raise HTTPException(
            status_code=404,
            detail=f"El cliente no posee una membresía {status.value}"
        )

    return membership


@router.get(
    "/{customer_id}",
    response_model=CustomerMembershipRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener la membresía de un cliente",
    description="""
    Devuelve la membresía de un cliente específico según el estado solicitado.

    - Solo accesible por administradores.
    - Permite consultar la membresía activa, pendiente o inactiva.
    - Por defecto devuelve la membresía activa.
    - Se utiliza para soporte, administración o auditoría.
    """,
    responses={
        200: {"description": "Membresía obtenida correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo administradores)"},
        404: {"description": "Cliente o membresía no encontrada"},
    },
)
def get_customer_membership(
    customer_id: int,
    session: SessionDep,
    status: MembershipStatusEnum = MembershipStatusEnum.ACTIVE,
    admin: User = Depends(check_admin),
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
        raise HTTPException(
            404,
            f"El customer no posee una membresía {status.value}"
        )

    return membership


