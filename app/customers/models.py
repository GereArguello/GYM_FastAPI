from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from app.core.enums import StatusEnum

# SOLO PARA IDE, EVITA IMPORTS CIRCULARES
if TYPE_CHECKING:
    from app.memberships.models import Membership, CustomerMembership
    from app.attendances.models import Attendance
    from app.redemptions.models import Redemption



class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)

    first_name: str
    last_name: str
    birth_date: date
    points_balance: int = Field(default=0)
    is_active: StatusEnum = Field(default=StatusEnum.ACTIVE)

    attendances: list["Attendance"] = Relationship(back_populates="customer")
    memberships: list["CustomerMembership"] = Relationship(back_populates="customer")
    redemptions: list["Redemption"] = Relationship(back_populates="customer")

    @property
    def active_membership(self) -> Optional["CustomerMembership"]:
        return next(
            (cm for cm in self.memberships if cm.is_active),
            None)



class CustomerMembership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    customer_id: int = Field(foreign_key="customer.id")
    membership_id: int = Field(foreign_key="membership.id")

    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    is_active: bool = Field(default=True)

    customer: "Customer" = Relationship(back_populates="memberships")
    membership: "Membership" = Relationship(back_populates="customer_memberships")


