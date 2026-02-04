from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import date
from app.core.enums import MembershipStatusEnum

if TYPE_CHECKING:
    from app.customers.models import Customer
    from app.memberships.models import Membership
    from app.attendances.models import Attendance


class CustomerMembership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    customer_id: int = Field(foreign_key="customer.id")
    membership_id: int = Field(foreign_key="membership.id")

    status: MembershipStatusEnum = Field(default=MembershipStatusEnum.ACTIVE)

    start_date: date
    end_date: Optional[date] = Field(default=None)

    customer: "Customer" = Relationship(back_populates="memberships")
    membership: "Membership" = Relationship(back_populates="customer_memberships")

    attendances: list["Attendance"] = Relationship(back_populates="customer_membership")
