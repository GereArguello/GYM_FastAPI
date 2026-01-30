from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.memberships.schemas import MembershipRead, MembershipCreate, MembershipUpdate
from app.memberships.models import Membership
from app.core.database import SessionDep
from app.core.enums import RoleEnum, StatusEnum
from app.auth.dependencies import check_admin, get_current_user_optional
from app.auth.models import User



router = APIRouter(
    prefix="/memberships",
    tags=["memberships"]
)

@router.post(
    "/",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva membresía",
    description="""
    Crea una nueva membresía en el sistema.

    - Solo accesible por administradores.
    - El nombre de la membresía debe ser único.
    - La membresía se crea en estado ACTIVE por defecto.
    - Define reglas como días máximos por semana y multiplicador de puntos.
    """,
    responses={
        201: {"description": "Membresía creada correctamente"},
        400: {"description": "Datos de membresía inválidos o duplicados"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo administradores)"},
    },
)
def create_membership(
    membership_data: MembershipCreate,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    membership = Membership(**membership_data.model_dump())

    try:
        session.add(membership)
        session.commit()
        session.refresh(membership)
        return membership
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos de membresía inválidos"
        )

    
@router.get(
    "/",
    response_model=list[MembershipRead],
    status_code=status.HTTP_200_OK,
    summary="Listar membresías",
    description="""
    Devuelve la lista de membresías disponibles en el sistema.

    Comportamiento según rol:
    - Administradores: pueden ver todas las membresías y filtrar por estado.
    - Usuarios públicos o clientes: solo ven membresías activas.

    Filtros:
    - `status`: filtra por estado (solo para administradores).
    - `search`: filtra por nombre de la membresía.
    """,
    responses={
        200: {"description": "Lista de membresías obtenida correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
    },
)
def list_memberships(
    session: SessionDep,
    status: StatusEnum | None = None,
    search: str | None = None,
    current_user: User | None = Depends(get_current_user_optional),
):
    query = select(Membership)

    if current_user and current_user.role == RoleEnum.ADMIN:
        if status:
            query = query.where(Membership.status == status)
    else:
        query = query.where(Membership.status == StatusEnum.ACTIVE)

    if search:
        query = query.where(Membership.name.ilike(f"%{search}%"))

    return session.exec(query).all()


@router.get(
    "/{membership_id}",
    response_model=MembershipRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener una membresía por ID",
    description="""
    Devuelve la información de una membresía específica.

    Comportamiento según rol:
    - Administradores: pueden acceder a membresías activas o inactivas
      usando el parámetro `include_inactive=true`.
    - Usuarios públicos o clientes: solo pueden acceder a membresías activas.

    Parámetros:
    - `include_inactive`: permite incluir membresías inactivas (solo admin).
    """,
    responses={
        200: {"description": "Membresía obtenida correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        404: {"description": "Membresía no encontrada"},
    },
)
def read_membership(
    membership_id: int,
    session: SessionDep,
    include_inactive: bool = False,
    current_user: User | None = Depends(get_current_user_optional),
):
    query = select(Membership).where(Membership.id == membership_id)

    if not (current_user and current_user.role == RoleEnum.ADMIN and include_inactive):
        query = query.where(Membership.status == StatusEnum.ACTIVE)

    membership = session.exec(query).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membresía no encontrada"
        )

    return membership


@router.patch(
    "/{membership_id}",
    response_model=MembershipRead,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una membresía",
    description="""
    Permite actualizar parcialmente una membresía existente.

    - Solo accesible por administradores.
    - Solo se actualizan los campos enviados.
    - No crea una nueva membresía, modifica la existente.
    - Mantiene el estado actual de la membresía si no se envía `status`.
    """,
    responses={
        200: {"description": "Membresía actualizada correctamente"},
        400: {"description": "Datos de membresía inválidos"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo administradores)"},
        404: {"description": "Membresía no encontrada"},
    },
)
def update_membership(
    membership_id: int,
    membership_data: MembershipUpdate,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    membership = session.get(Membership, membership_id)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membresía no encontrada"
        )

    update_data = membership_data.model_dump(exclude_unset=True)

    membership.sqlmodel_update(update_data)

    try:
        session.commit()
        session.refresh(membership)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos de membresía inválidos"
        )

    return membership

@router.delete(
    "/{membership_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar una membresía",
    description="""
    Desactiva una membresía existente del sistema.

    - Solo accesible por administradores.
    - No elimina el registro de la base de datos (soft delete).
    - La membresía pasa al estado INACTIVE.
    - Las membresías inactivas no se muestran a usuarios públicos.
    """,
    responses={
        204: {"description": "Membresía desactivada correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo administradores)"},
        404: {"description": "Membresía no encontrada"},
    },
)
def delete_membership(
    membership_id: int,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    membership = session.get(Membership, membership_id)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membresía no encontrada"
        )

    membership.status = StatusEnum.INACTIVE
    session.commit()
