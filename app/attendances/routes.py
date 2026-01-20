from fastapi import APIRouter, status, HTTPException
from typing import Optional, List
from sqlmodel import select, desc
from datetime import datetime, timezone
from app.attendances.schemas import AttendanceRead, AttendanceCreate
from app.attendances.models import Attendance
from app.customers.models import Customer, CustomerMembership
from app.core.database import SessionDep


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
    
    if attendance.check_out:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Asistencia ya finalizada")
    
    attendance.check_out = datetime.now(timezone.utc)

    #Normalizar tz
    if attendance.check_in.tzinfo is None:
        attendance.check_in = attendance.check_in.replace(tzinfo=timezone.utc)

    # calcular tiempo de asistencia
    td = attendance.check_out - attendance.check_in
    minutos_totales = td.total_seconds() / 60
    attendance.duration_minutes = int(minutos_totales)

    if attendance.duration_minutes >= 300:
        attendance.is_valid = False
    elif attendance.duration_minutes < 30:
        attendance.is_valid = False
    else:
        attendance.is_valid = True
    
    # HARDCODEADA COMO REFERENCIA
    if attendance.is_valid and attendance.membership_id:
        attendance.points_awarded = 10 * attendance.membership.points_multiplier
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




    
    
    