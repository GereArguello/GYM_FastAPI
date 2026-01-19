from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime


if TYPE_CHECKING:
    from customers.models import Customer
    from memberships.models import Membership

class Attendance(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    customer_id : int = Field(
        foreign_key="customer.id", nullable=False
    )
    membership_id : Optional[int] = Field(foreign_key="membership.id", nullable=True)

    customer: "Customer" = Relationship(back_populates="attendances")
    membership: Optional["Membership"] = Relationship(back_populates="attendances")

    check_in : datetime
    check_out : datetime | None = None

    duration_minutes : int | None = None
    points_awarded : int | None = None
    is_valid : bool = False