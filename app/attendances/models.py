from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime


if TYPE_CHECKING:
    from customers.models import Customer

class Attendance(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    customer_id : int = Field(
        foreign_key="customer.id", nullable=False
    )
    customer: "Customer" = Relationship(back_populates="attendances")

    check_in : datetime
    check_out : datetime | None = None

    duration_minutes : int | None = None
    points_awarded : int
    is_valid : bool = False