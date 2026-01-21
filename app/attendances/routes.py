from fastapi import APIRouter, status, HTTPException
from typing import Optional, List
from sqlmodel import select, desc
from datetime import datetime, timezone
from app.attendances.schemas import AttendanceRead, AttendanceCreate
from app.attendances.models import Attendance
from app.customers.models import Customer, CustomerMembership
from app.core.database import SessionDep
from app.attendances.services import (finalize_attendance, 
                                      get_weekly_attendance_count,
                                      normalize_datetime)


router = APIRouter(
    prefix="/attendances",
    tags=["attendances"]
)

@router.post("/", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def create_attendance(
    data: AttendanceCreate,
    session: SessionDep
):
    customer = session.get(Customer, data.customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer no encontrado"
        )

    customer_membership = session.exec(
        select(CustomerMembership)
        .where(
            CustomerMembership.customer_id == customer.id,
            CustomerMembership.is_active == True
        )
    ).first()

    if not customer_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer no tiene membresía activa"
        )
    
    count_attendances = get_weekly_attendance_count(session, customer.id)

    if count_attendances >= customer_membership.membership.max_days_per_week:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Límite semanal de asistencias alcanzado")

    attendance = Attendance(
        customer_id=customer.id,
        membership_id=customer_membership.membership_id,
        check_in = datetime.now(timezone.utc)
    )

    session.add(attendance)
    session.commit()
    session.refresh(attendance)

    return attendance

@router.patch("/{attendance_id}/checkout", response_model=AttendanceRead, status_code=status.HTTP_200_OK)
def checkout_attendance(attendance_id: int, session: SessionDep):
    attendance = session.get(Attendance, attendance_id)

    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Asistencia no encontrada")
    
    customer = session.get(Customer, attendance.customer_id)

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Customer no encontrado")
    
    if attendance.check_out:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Asistencia ya finalizada")

    #Normalizar tz
    attendance.check_out = normalize_datetime(datetime.now(timezone.utc))
    attendance.check_in = normalize_datetime(attendance.check_in)

    # calcular tiempo de asistencia
    finalize_attendance(attendance)
    
    # HARDCODEADA COMO REFERENCIA
    if attendance.is_valid and attendance.membership_id:
        attendance.points_awarded = 10 * attendance.membership.points_multiplier
        customer.points_balance += attendance.points_awarded
    else:
        attendance.points_awarded = 0
    
    session.commit()
    session.refresh(attendance)

    return attendance

@router.get("/", response_model=List[AttendanceRead], status_code=status.HTTP_200_OK)
def list_attendances(session: SessionDep, customer_id : Optional[int] = None):
    query = select(Attendance).order_by(desc(Attendance.check_in))

    if customer_id is not None:
        query = query.where(Attendance.customer_id == customer_id)

    return session.exec(query).all()

@router.get("/{attendance_id}", response_model=AttendanceRead,status_code=status.HTTP_200_OK)
def read_attendance(attendance_id: int, session: SessionDep):
    attendance = session.get(Attendance, attendance_id)

    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Asistencia no encontrada")
    
    return attendance

