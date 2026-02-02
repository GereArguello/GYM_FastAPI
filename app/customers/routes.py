from fastapi import APIRouter, status, HTTPException, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from app.core.database import SessionDep
from app.core.enums import StatusEnum
from app.core.pagination import DefaultPagination
from app.customers.models import Customer
from app.customers.schemas import CustomerCreate, CustomerRead, CustomerUpdate
from app.customers.services import register_customer
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


    

