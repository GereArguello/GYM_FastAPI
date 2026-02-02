from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String
from app.core.enums import StatusEnum, MembershipStatusEnum

# SOLO PARA IDE, EVITA IMPORTS CIRCULARES
if TYPE_CHECKING:
    from app.customermemberships.models import CustomerMembership
    from app.attendances.models import Attendance
    from app.redemptions.models import Redemption



class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)

    first_name: str = Field(sa_column=Column(String(100), nullable=False))
    last_name: str = Field(sa_column=Column(String(100), nullable=False))
    birth_date: date
    points_balance: int = Field(default=0)
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)

    attendances: list["Attendance"] = Relationship(back_populates="customer")
    memberships: list["CustomerMembership"] = Relationship(back_populates="customer")
    redemptions: list["Redemption"] = Relationship(back_populates="customer")

    @property
    def active_membership(self) -> Optional["CustomerMembership"]:
        return next(
            (cm for cm in self.memberships if cm.status == MembershipStatusEnum.ACTIVE),
            None)



