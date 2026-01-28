from sqlmodel import select, Session
from datetime import date, datetime, timedelta, timezone
from app.attendances.models import Attendance
from app.customers.models import Customer

def finalize_attendance(attendance: Attendance) -> None:
    td = attendance.check_out - attendance.check_in
    attendance.duration_minutes = int(td.total_seconds() / 60)
    attendance.is_valid = 30 <= attendance.duration_minutes < 300

def apply_attendance_points(attendance: Attendance, customer: Customer):
    active_membership = attendance.customer.active_membership

    if attendance.is_valid and active_membership:
        attendance.membership = active_membership.membership
        attendance.membership_id = active_membership.membership_id
        attendance.points_awarded = 10 * active_membership.membership.points_multiplier
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
