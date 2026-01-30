from fastapi import APIRouter, status, HTTPException, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from sqlmodel import select, desc
from app.redemptions.models import Redemption
from app.redemptions.schemas import RedemptionRead, RedemptionCreate
from app.shop.models import Product
from app.customers.models import Customer
from app.core.database import SessionDep
from app.core.enums import ProductType, RoleEnum, StatusEnum
from app.core.pagination import DefaultPagination
from app.auth.dependencies import get_current_customer, check_admin, get_current_user
from app.auth.models import User


router = APIRouter(prefix="/redemptions",
                   tags=["redemptions"])

@router.post(
    "/",
    response_model=RedemptionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Canjear producto por puntos",
    description="""
    Registra un canje de producto utilizando puntos del cliente.

    Características:
    - Solo accesible para clientes autenticados.
    - Permite canjear productos del tipo POINTS.
    - Valida disponibilidad, stock y saldo de puntos.
    - Descuenta los puntos del cliente y el stock del producto.
    - Registra un snapshot del nombre del producto al momento del canje.

    Reglas de negocio:
    - El producto debe existir y estar activo.
    - El producto debe ser canjeable por puntos.
    - La cantidad debe ser mayor a cero.
    - Debe existir stock suficiente.
    - El cliente debe tener puntos suficientes para el canje.

    Requiere:
    - Autenticación con token Bearer.
    - Rol CUSTOMER.
    """,
    responses={
        201: {"description": "Canje realizado correctamente"},
        400: {"description": "Datos inválidos (cantidad inválida)"},
        401: {"description": "No autenticado"},
        404: {"description": "Producto no encontrado"},
        409: {"description": "Conflicto de negocio (producto no disponible, stock o puntos insuficientes)"},
    },
)
def create_redemption(
    data: RedemptionCreate,
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
):
    product = session.get(Product, data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    if product.status != StatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Producto no disponible"
        )

    if product.product_type != ProductType.POINTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este producto no es canjeable por puntos"
        )

    if data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad debe ser mayor a cero"
        )

    if product.stock < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No hay stock suficiente"
        )

    customer_points = current_customer.points_balance
    redemption_cost = product.price * data.quantity

    if customer_points < redemption_cost:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No tienes puntos suficientes"
        )

    current_customer.points_balance -= redemption_cost
    product.stock -= data.quantity

    redemption = Redemption(
        customer_id=current_customer.id,
        product_id=data.product_id,
        points_spent=redemption_cost,
        quantity=data.quantity,
        product_name_snapshot=product.name,
    )

    session.add(redemption)
    session.commit()
    session.refresh(redemption)

    return redemption


@router.get(
    "/",
    response_model=Page[RedemptionRead],
    status_code=status.HTTP_200_OK,
    summary="Listar canjes",
    description="""
    Devuelve una lista paginada de todos los canjes registrados en el sistema.

    Características:
    - Solo accesible para administradores.
    - Permite consultar el historial completo de canjes.
    - Útil para auditoría, control de stock y análisis de consumo.
    - Resultados ordenados por fecha de creación descendente.

    Requiere:
    - Autenticación con token Bearer.
    - Rol ADMIN.
    """,
    responses={
        200: {"description": "Listado de canjes obtenido correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo admin)"},
    },
)
def list_redemptions(
    session: SessionDep,
    admin: User = Depends(check_admin),
    params: DefaultPagination = Depends(),
):
    query = select(Redemption).order_by(desc(Redemption.id))
    return paginate(session, query, params)


@router.get(
    "/me",
    response_model=Page[RedemptionRead],
    status_code=status.HTTP_200_OK,
    summary="Listar mis canjes",
    description="""
    Devuelve una lista paginada de los canjes realizados por el cliente autenticado.

    Características:
    - Solo accesible para clientes autenticados.
    - Devuelve únicamente los canjes asociados al cliente actual.
    - Útil para consultar historial de consumo y puntos utilizados.
    - Resultados ordenados por fecha de creación descendente.

    Requiere:
    - Autenticación con token Bearer.
    - Rol CUSTOMER.
    """,
    responses={
        200: {"description": "Listado de canjes obtenido correctamente"},
        401: {"description": "No autenticado"},
    },
)
def list_my_redemptions(
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
    params: DefaultPagination = Depends(),
):
    query = (
        select(Redemption)
        .where(Redemption.customer_id == current_customer.id)
        .order_by(desc(Redemption.id))
    )

    return paginate(session, query, params)


@router.get(
    "/{redemption_id}",
    response_model=RedemptionRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener canje por ID",
    description="""
    Devuelve el detalle completo de un canje específico.

    Características:
    - Accesible para usuarios autenticados.
    - Los administradores pueden consultar cualquier canje.
    - Los clientes solo pueden acceder a sus propios canjes.
    - Para usuarios no autorizados, el canje se comporta como inexistente.

    Comportamiento según rol:
    - Rol ADMIN: acceso total a cualquier canje.
    - Rol CUSTOMER: acceso únicamente a canjes propios.

    Requiere:
    - Autenticación con token Bearer.
    """,
    responses={
        200: {"description": "Canje obtenido correctamente"},
        401: {"description": "No autenticado"},
        404: {"description": "Canje no encontrado"},
    },
)
def read_redemption(
    redemption_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
):
    redemption = session.get(Redemption, redemption_id)
    if not redemption:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canje no encontrado"
        )

    # Acceso total para administradores
    if current_user.role == RoleEnum.ADMIN:
        return redemption

    # Acceso restringido al cliente propietario del canje
    customer = session.exec(
        select(Customer).where(Customer.user_id == current_user.id)
    ).first()

    if not customer or redemption.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canje no encontrado"
        )

    return redemption

