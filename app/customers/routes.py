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


@router.post(
    "/",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo cliente",
    description="""
    Crea un nuevo cliente junto con su usuario asociado.

    - El email debe ser único en el sistema.
    - Se crea primero el usuario y luego el customer.
    - El cliente queda activo por defecto.
    """,
    responses={
        201: {"description": "Cliente creado correctamente"},
        400: {"description": "El email ya está siendo utilizado"},
        422: {"description": "Datos de entrada inválidos"},
    },
)
def register_customer_endpoint(
    customer_data: CustomerCreate,
    session: SessionDep
):
    try:
        customer = register_customer(session, customer_data)
        return customer

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está siendo utilizado"
        )
    

@router.get(
    "/me",
    response_model=CustomerRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener mi perfil de cliente",
    description="""
    Devuelve la información del cliente autenticado actualmente.

    - Requiere autenticación con token Bearer.
    - El cliente se obtiene a partir del usuario autenticado.
    - Solo devuelve el perfil propio (no permite acceder a otros clientes).
    """,
    responses={
        200: {"description": "Perfil del cliente obtenido correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Token inválido o sin permisos"},
    },
)
def read_me(
    current_customer: Customer = Depends(get_current_customer)
):
    return current_customer


@router.get(
    "/",
    response_model=Page[CustomerRead],
    status_code=status.HTTP_200_OK,
    summary="Listar clientes",
    description="""
    Devuelve una lista paginada de clientes del sistema.

    - Solo accesible por administradores.
    - Permite filtrar por estado (activo / inactivo).
    - Permite buscar por nombre o apellido.
    - Los resultados están ordenados por apellido y nombre.
    """,
    responses={
        200: {"description": "Lista de clientes obtenida correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo administradores)"},
    },
)
def list_customers(
    session: SessionDep,
    status: StatusEnum | None = None,
    search: str | None = None,
    admin: User = Depends(check_admin),
    params: DefaultPagination = Depends(),
):
    query = select(Customer)

    if status:
        query = query.where(Customer.status == status)

    if search:
        query = query.where(
            (Customer.first_name.ilike(f"%{search}%")) |
            (Customer.last_name.ilike(f"%{search}%"))
        )

    query = query.order_by(Customer.last_name, Customer.first_name)

    return paginate(session, query, params)


@router.patch(
    "/me",
    response_model=CustomerRead,
    status_code=status.HTTP_200_OK,
    summary="Actualizar mi perfil de cliente",
    description="""
    Permite al cliente autenticado actualizar su propia información personal.

    - Solo se actualizan los campos enviados.
    - No permite modificar datos de otros clientes.
    - Requiere autenticación con token Bearer.
    """,
    responses={
        200: {"description": "Perfil del cliente actualizado correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Token inválido o sin permisos"},
        422: {"description": "Datos de entrada inválidos"},
    },
)
def update_customer(
    customer_data: CustomerUpdate,
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
):
    update_data = customer_data.model_dump(exclude_unset=True)

    current_customer.sqlmodel_update(update_data)

    session.commit()
    session.refresh(current_customer)

    return current_customer


@router.delete(
    "/me/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar mi cuenta de cliente",
    description="""
    Desactiva la cuenta del cliente autenticado.

    - No elimina el registro de la base de datos (soft delete).
    - El estado del cliente pasa a INACTIVE.
    - El cliente no podrá acceder nuevamente al sistema.
    - Requiere autenticación con token Bearer.
    """,
    responses={
        204: {"description": "Cuenta desactivada correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Token inválido o sin permisos"},
    },
)
def deactivate_customer_me(
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
):
    current_customer.status = StatusEnum.INACTIVE
    session.commit()


#---------ENDPOINTS PARA RELACIONAR CUSTOMERS Y MEMBERSHIPS----------#


@router.post(
    "/assign-membership/{membership_id}",
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
    "/customer-memberships",
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
    "/me/membership",
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
    "/{customer_id}/membership",
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


#rutas dinámicas van al final
@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener un cliente por ID",
    description="""
    Devuelve la información de un cliente específico.

    - Solo accesible por administradores.
    - Solo devuelve clientes activos.
    - No permite consultar clientes inactivos (soft deleted).
    - Se utiliza para administración y soporte.
    """,
    responses={
        200: {"description": "Cliente obtenido correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo administradores)"},
        404: {"description": "Cliente no encontrado"},
    },
)
def read_customer(
    customer_id: int,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    customer = session.get(Customer, customer_id)
    if not customer or customer.status != StatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    return customer


    

