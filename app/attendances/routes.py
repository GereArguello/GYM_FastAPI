from fastapi import APIRouter, status, HTTPException, Depends
from typing import Optional, List
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
from app.auth.dependencies import get_current_customer, check_admin
from app.auth.models import User


router = APIRouter(
    prefix="/attendances",
    tags=["attendances"]
)

@router.post("/", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def create_attendance(
    session: SessionDep,
    current_customer: Customer = Depends(get_current_customer)
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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ya tenés una asistencia activa")

    count_attendances = get_weekly_attendance_count(session, current_customer.id)

    if count_attendances >= customer_membership.membership.max_days_per_week:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Límite semanal de asistencias alcanzado")

    attendance = Attendance(
        customer_id=current_customer.id,
        membership_id=customer_membership.membership_id,
        check_in = datetime.now(timezone.utc)
    )

    session.add(attendance)
    session.commit()
    session.refresh(attendance)

    return attendance

@router.patch("/{attendance_id}/checkout", response_model=AttendanceRead, status_code=status.HTTP_200_OK)
def checkout_attendance(attendance_id: int,
                        session: SessionDep,
                        current_customer: Customer = Depends(get_current_customer)):
    attendance = session.get(Attendance, attendance_id)

    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Asistencia no encontrada")
    
    if attendance.customer_id != current_customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permiso para finalizar esta asistencia"
        )
    
    if attendance.check_out:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Asistencia ya finalizada")

    # NUEVA REGLA
    today = datetime.now(timezone.utc).date()
    check_in_day = attendance.check_in.date()

    if check_in_day != today:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede finalizar una asistencia de un día anterior"
        )

    #Normalizar tz
    attendance.check_out = normalize_datetime(datetime.now(timezone.utc))
    attendance.check_in = normalize_datetime(attendance.check_in)

    # calcular tiempo de asistencia
    finalize_attendance(attendance)
    
    # HARDCODEADA COMO REFERENCIA
    apply_attendance_points(attendance, current_customer)
    
    session.commit()
    session.refresh(attendance)

    return attendance

@router.get("/", response_model=List[AttendanceRead], status_code=status.HTTP_200_OK)
def list_attendances(session: SessionDep,
                     customer_id : Optional[int] = None,
                     admin: User = Depends(check_admin)):
    query = select(Attendance).order_by(desc(Attendance.check_in))

    if customer_id is not None:
        query = query.where(Attendance.customer_id == customer_id)

    return session.exec(query).all()

@router.get("/me", response_model=list[AttendanceRead], status_code=status.HTTP_200_OK)
def read_me_attendances(session: SessionDep,
                        current_customer: Customer = Depends(get_current_customer)):
    
    query = select(Attendance).where(Attendance.customer_id == current_customer.id).order_by(desc(Attendance.check_in))

    return session.exec(query).all()

@router.get("/{attendance_id}", response_model=AttendanceRead,status_code=status.HTTP_200_OK)
def read_attendance(attendance_id: int,
                    session: SessionDep,
                    admin: User = Depends(check_admin)):
    attendance = session.get(Attendance, attendance_id)

    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Asistencia no encontrada")
    
    return attendance

