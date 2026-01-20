from sqlmodel import select
from datetime import datetime, timedelta, timezone
from app.attendances.models import Attendance


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