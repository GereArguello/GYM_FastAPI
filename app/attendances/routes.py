from fastapi import APIRouter, status, HTTPException, Depends
from typing import Optional, List
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from sqlmodel import select, desc
from datetime import datetime, timezone
from app.attendances.schemas import AttendanceRead
from app.attendances.models import Attendance
from app.customers.models import Customer, CustomerMembership
from app.attendances.services import (finalize_attendance, 
                                      get_weekly_attendance_count,
                                      normalize_datetime,
                                      apply_attendance_points,
                                      get_open_attendance_today)
from app.core.database import SessionDep
from app.core.enums import MembershipStatusEnum
from app.core.pagination import DefaultPagination
from app.auth.dependencies import get_current_customer, check_admin
from app.auth.models import User


router = APIRouter(
    prefix="/attendances",
    tags=["attendances"]
)

@router.post(
    "/",
    response_model=AttendanceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una asistencia (check-in)",
    description="""
    Registra una nueva asistencia del cliente autenticado.

    Reglas:
    - El cliente debe tener una membresía activa.
    - Solo puede existir una asistencia abierta por día.
    - Se respeta el límite semanal de asistencias definido por la membresía.
    - La asistencia se registra con fecha y hora de check-in en UTC.

    Este endpoint representa el ingreso del cliente al gimnasio.
    """,
    responses={
        201: {"description": "Asistencia registrada correctamente"},
        403: {"description": "El cliente no posee una membresía activa"},
        409: {"description": "Conflicto: asistencia activa o límite semanal alcanzado"},
        401: {"description": "No autenticado"},
    },
)
def create_attendance(
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
):
    customer_membership = session.exec(
        select(CustomerMembership)
        .where(
            CustomerMembership.customer_id == current_customer.id,
            CustomerMembership.status == MembershipStatusEnum.ACTIVE
        )
    ).first()

    if not customer_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer no tiene membresía activa"
        )
    
    open_attendance = get_open_attendance_today(session, current_customer.id)
    if open_attendance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tenés una asistencia activa"
        )

    count_attendances = get_weekly_attendance_count(session, current_customer.id)

    if count_attendances >= customer_membership.membership.max_days_per_week:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Límite semanal de asistencias alcanzado"
        )

    attendance = Attendance(
        customer_id=current_customer.id,
        membership_id=customer_membership.membership_id,
        check_in=datetime.now(timezone.utc),
    )

    session.add(attendance)
    session.commit()
    session.refresh(attendance)

    return attendance


@router.patch(
    "/{attendance_id}/checkout",
    response_model=AttendanceRead,
    status_code=status.HTTP_200_OK,
    summary="Finalizar asistencia (check-out)",
    description="""
    Finaliza una asistencia activa del cliente autenticado.

    Reglas:
    - La asistencia debe existir.
    - Solo el dueño de la asistencia puede finalizarla.
    - No se puede finalizar una asistencia ya cerrada.
    - No se puede finalizar una asistencia de un día anterior.
    - El checkout se normaliza a UTC.
    - Se calcula la duración total de la asistencia.
    - Se aplican puntos al cliente (regla actual hardcodeada).

    Este endpoint representa la salida del cliente del gimnasio.
    """,
    responses={
        200: {"description": "Asistencia finalizada correctamente"},
        403: {"description": "No tenés permiso para finalizar esta asistencia"},
        404: {"description": "Asistencia no encontrada"},
        409: {"description": "Conflicto de estado (asistencia ya cerrada o de otro día)"},
        401: {"description": "No autenticado"},
    },
)
def checkout_attendance(
    attendance_id: int,
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
):
    attendance = session.get(Attendance, attendance_id)

    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asistencia no encontrada"
        )
    
    if attendance.customer_id != current_customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permiso para finalizar esta asistencia"
        )
    
    if attendance.check_out:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asistencia ya finalizada"
        )

    # NUEVA REGLA
    today = datetime.now(timezone.utc).date()
    check_in_day = attendance.check_in.date()

    if check_in_day != today:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede finalizar una asistencia de un día anterior"
        )

    # Normalizar tz
    attendance.check_out = normalize_datetime(datetime.now(timezone.utc))
    attendance.check_in = normalize_datetime(attendance.check_in)

    # calcular tiempo de asistencia
    finalize_attendance(attendance)
    
    # HARDCODEADA COMO REFERENCIA
    apply_attendance_points(attendance, current_customer)
    
    session.commit()
    session.refresh(attendance)

    return attendance

@router.get(
    "/",
    response_model=Page[AttendanceRead],
    status_code=status.HTTP_200_OK,
    summary="Listar asistencias",
    description="""
    Devuelve un listado paginado de asistencias registradas en el sistema.

    Características:
    - Solo accesible para administradores.
    - Permite filtrar asistencias por cliente usando `customer_id`.
    - Los resultados se ordenan por fecha de check-in descendente (más recientes primero).
    - Soporta paginación mediante parámetros estándar (`page`, `size`).

    Útil para:
    - Auditoría de asistencias.
    - Control de uso del gimnasio.
    - Reportes administrativos.
    """,
    responses={
        200: {"description": "Listado de asistencias obtenido correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo administradores)"},
    },
)
def list_attendances(
    session: SessionDep,
    customer_id: Optional[int] = None,
    admin: User = Depends(check_admin),
    params: DefaultPagination = Depends(),
):
    query = select(Attendance)

    if customer_id is not None:
        query = query.where(Attendance.customer_id == customer_id)

    query = query.order_by(desc(Attendance.check_in))
    return paginate(session, query, params)


@router.get(
    "/me",
    response_model=Page[AttendanceRead],
    status_code=status.HTTP_200_OK,
    summary="Listar mis asistencias",
    description="""
    Devuelve un listado paginado de las asistencias del cliente autenticado.

    Características:
    - Solo devuelve asistencias del usuario autenticado.
    - Requiere autenticación con token Bearer.
    - Los resultados se ordenan por fecha de check-in descendente (más recientes primero).
    - Soporta paginación mediante parámetros estándar (`page`, `size`).

    Útil para:
    - Que el cliente consulte su historial de entrenamientos.
    - Seguimiento personal de asistencia.
    - Visualización en app o dashboard de usuario.
    """,
    responses={
        200: {"description": "Listado de asistencias obtenido correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Token inválido o sin permisos"},
    },
)
def read_me_attendances(
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer),
    params: DefaultPagination = Depends(),
):
    query = (
        select(Attendance)
        .where(Attendance.customer_id == current_customer.id)
        .order_by(desc(Attendance.check_in))
    )

    return paginate(session, query, params)


@router.get(
    "/{attendance_id}",
    response_model=AttendanceRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener asistencia por ID",
    description="""
    Devuelve el detalle completo de una asistencia específica.

    Características:
    - Solo accesible para administradores.
    - Permite consultar cualquier asistencia por su ID.
    - Útil para auditorías, soporte o revisión de historial.
    - Devuelve información de check-in, check-out y duración.

    Requiere:
    - Autenticación con token Bearer.
    - Rol ADMIN.
    """,
    responses={
        200: {"description": "Asistencia obtenida correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado (solo admin)"},
        404: {"description": "Asistencia no encontrada"},
    },
)
def read_attendance(
    attendance_id: int,
    session: SessionDep,
    admin: User = Depends(check_admin),
):
    attendance = session.get(Attendance, attendance_id)

    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asistencia no encontrada"
        )

    return attendance


