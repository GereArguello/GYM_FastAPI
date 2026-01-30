from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from app.core.database import SessionDep
from app.core.enums import RoleEnum, StatusEnum
from app.core.pagination import ProductPagination
from app.shop.models import Product
from app.shop.schemas import ProductRead, ProductCreate, ProductUpdate
from app.auth.models import User
from app.auth.dependencies import check_admin, get_current_user_optional


router = APIRouter(prefix="/shop",
                   tags=["shop"])

@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo producto",
    description="""
    Crea un nuevo producto en el sistema.

    Características:
    - Solo accesible para administradores.
    - Permite registrar productos canjeables o de uso interno.
    - Valida que no exista otro producto con el mismo nombre.
    - El producto se crea con estado activo por defecto.

    Requiere:
    - Autenticación con token Bearer.
    - Rol ADMIN.
    """,
    responses={
        201: {"description": "Producto creado correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo admin)"},
        409: {"description": "Ya existe un producto con ese nombre"},
    },
)
def create_product(
    product_data: ProductCreate,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    product = Product(**product_data.model_dump())

    try:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un producto con ese nombre"
        )


@router.get(
    "/",
    response_model=Page[ProductRead],
    status_code=status.HTTP_200_OK,
    summary="Listar productos",
    description="""
    Devuelve una lista paginada de productos.

    Características:
    - Endpoint público (no requiere autenticación).
    - Por defecto solo devuelve productos activos.
    - Los usuarios administradores pueden incluir productos inactivos.
    - Resultados ordenados por precio y luego por ID.
    - Soporta paginación mediante parámetros personalizados.

    Comportamiento según rol:
    - Usuarios no autenticados: solo productos activos.
    - Usuarios autenticados sin rol ADMIN: solo productos activos.
    - Usuarios ADMIN: pueden incluir productos inactivos usando `include_inactive=true`.

    Requiere:
    - Autenticación opcional.
    """,
    responses={
        200: {"description": "Listado de productos obtenido correctamente"},
        401: {"description": "No autenticado"},
    },
)
def list_products(
    session: SessionDep,
    include_inactive: bool = False,
    current_user: User | None = Depends(get_current_user_optional),
    params: ProductPagination = Depends(),
):
    query = select(Product)

    # Solo admin puede ver inactivos explícitamente
    if not (current_user and current_user.role == RoleEnum.ADMIN and include_inactive):
        query = query.where(Product.status == StatusEnum.ACTIVE)

    query = query.order_by(Product.price, Product.id)

    return paginate(session, query, params)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener producto por ID",
    description="""
    Devuelve el detalle completo de un producto específico.

    Características:
    - Endpoint público (no requiere autenticación).
    - Permite consultar un producto por su ID.
    - Los productos inactivos solo son visibles para administradores.
    - Para usuarios no autorizados, los productos inactivos se comportan como inexistentes.

    Comportamiento según rol:
    - Usuarios no autenticados: solo pueden acceder a productos activos.
    - Usuarios autenticados sin rol ADMIN: solo pueden acceder a productos activos.
    - Usuarios ADMIN: pueden acceder a productos activos e inactivos.

    Requiere:
    - Autenticación opcional.
    """,
    responses={
        200: {"description": "Producto obtenido correctamente"},
        401: {"description": "No autenticado"},
        404: {"description": "Producto no encontrado"},
    },
)
def read_product(
    product_id: int,
    session: SessionDep,
    current_user: User | None = Depends(get_current_user_optional),
):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    # Bloqueo de productos inactivos para usuarios no admin
    if (
        product.status != StatusEnum.ACTIVE
        and not (current_user and current_user.role == RoleEnum.ADMIN)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    return product

    
@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Actualizar producto",
    description="""
    Actualiza parcialmente la información de un producto existente.

    Características:
    - Solo accesible para administradores.
    - Permite actualizar uno o más campos del producto.
    - Valida reglas de negocio como precios y stock no negativos.
    - Verifica unicidad del nombre si este es modificado.
    - Mantiene los valores actuales para los campos no enviados.

    Reglas de validación:
    - El precio no puede ser negativo.
    - El stock no puede ser negativo.
    - No se permiten nombres de producto duplicados.

    Requiere:
    - Autenticación con token Bearer.
    - Rol ADMIN.
    """,
    responses={
        200: {"description": "Producto actualizado correctamente"},
        400: {"description": "Datos inválidos (precio o stock negativo)"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo admin)"},
        404: {"description": "Producto no encontrado"},
        409: {"description": "Ya existe un producto con ese nombre"},
    },
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    # Solo validar si el nombre cambia
    if (
        product_data.name is not None
        and product_data.name != product.name
    ):
        product.name = product_data.name

    if product_data.description is not None:
        product.description = product_data.description

    if product_data.price is not None:
        if product_data.price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El precio no puede ser negativo"
            )
        product.price = product_data.price

    if product_data.stock is not None:
        if product_data.stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El stock no puede ser negativo"
            )
        product.stock = product_data.stock

    try:
        session.commit()
        session.refresh(product)
        return product

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un producto con ese nombre"
        )

    
@router.patch(
    "/{product_id}/activate",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Activar producto",
    description="""
    Activa un producto previamente inactivo.

    Características:
    - Solo accesible para administradores.
    - Cambia el estado del producto a ACTIVO.
    - Permite volver a habilitar productos que fueron desactivados.
    - No modifica otros campos del producto.

    Requiere:
    - Autenticación con token Bearer.
    - Rol ADMIN.
    """,
    responses={
        200: {"description": "Producto activado correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo admin)"},
        404: {"description": "Producto no encontrado"},
    },
)
def activate_product(
    product_id: int,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    product.status = StatusEnum.ACTIVE
    session.commit()
    session.refresh(product)
    return product

    
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar producto",
    description="""
    Desactiva un producto del sistema.

    La eliminación es lógica: el producto no se borra físicamente,
    sino que su estado pasa a INACTIVO.

    Características:
    - Solo accesible para administradores.
    - El producto desactivado no será visible para usuarios no administradores.
    - Permite preservar el historial y referencias del producto.
    - No devuelve contenido en la respuesta.

    Requiere:
    - Autenticación con token Bearer.
    - Rol ADMIN.
    """,
    responses={
        204: {"description": "Producto desactivado correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo admin)"},
        404: {"description": "Producto no encontrado"},
    },
)
def delete_product(
    product_id: int,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    product.status = StatusEnum.INACTIVE
    session.commit()
