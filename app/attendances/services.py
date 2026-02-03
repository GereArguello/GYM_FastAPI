from sqlmodel import select, Session
from datetime import date, datetime, timedelta, timezone
from app.attendances.models import Attendance
from app.customers.models import Customer
from app.core.constants import PUNTOS_BASE, ASISTENCIA_MINIMA, ASISTENCIA_MAXIMA

def finalize_attendance(attendance: Attendance) -> None:
    """
    Finaliza una asistencia calculando su duración y determinando su validez.

    La duración se calcula en minutos a partir del check-in y check-out.

    Regla de negocio actual (hardcodeada):
    - Una asistencia es válida si dura al menos 30 minutos
      y menos de 300 minutos (5 horas).

    Nota:
    - Estos valores podrían parametrizarse según la configuración del sistema.
    """
    td = attendance.check_out - attendance.check_in
    attendance.duration_minutes = int(td.total_seconds() / 60)
    attendance.is_valid = ASISTENCIA_MINIMA <= attendance.duration_minutes < ASISTENCIA_MAXIMA

def apply_attendance_points(attendance: Attendance, customer: Customer):
    """
    Aplica la asignación de puntos a una asistencia válida.

    Reglas de negocio:
    - Solo se otorgan puntos si la asistencia es válida.
    - El cliente debe tener una membresía activa.
    - Los puntos otorgados dependen del multiplicador de la membresía.
    - Los puntos se suman directamente al balance del cliente.

    Regla actual:
    - Se otorgan 10 puntos base por asistencia válida,
      multiplicados por el `points_multiplier` de la membresía.

    Nota:
    - Estos valores podrían parametrizarse según la configuración del sistema.
    """
    active_membership = attendance.customer.active_membership

    if attendance.is_valid and active_membership:
        attendance.membership = active_membership.membership
        attendance.membership_id = active_membership.membership_id
        attendance.points_awarded = PUNTOS_BASE * active_membership.membership.points_multiplier
        attendance.customer.points_balance += attendance.points_awarded
    else:
        attendance.points_awarded = 0

def normalize_datetime(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def get_weekly_attendance_count(
    session,
    customer_id: int,
    reference_time: datetime | None = None
) -> int:
    """
    Retorna el número de asistencias de un customer
    en la semana, en UTC
    """

    now = reference_time or datetime.now(timezone.utc)

    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    end_of_week = start_of_week + timedelta(days=7)

    return len(
        session.exec(
            select(Attendance)
            .where(
                Attendance.customer_id == customer_id,
                Attendance.check_in >= start_of_week,
                Attendance.check_in < end_of_week
            )
        ).all()
    )

def get_open_attendance_today(session: Session, customer_id: int) -> Attendance | None:
    """
    Obtiene la asistencia abierta del cliente para el día actual, si existe.
    """
    today = date.today()

    return session.exec(
        select(Attendance)
        .where(
            Attendance.customer_id == customer_id,
            Attendance.check_in >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
            Attendance.check_in <= datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc),
            Attendance.check_out == None
        )
    ).first()
