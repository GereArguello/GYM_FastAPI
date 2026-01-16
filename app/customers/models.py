from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from core.enums import StatusEnum

# SOLO PARA IDE, EVITA IMPORTS CIRCULARES
if TYPE_CHECKING:
    from memberships.models import Membership
    from attendances.models import Attendance


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    birth_date: date
    email: EmailStr = Field(nullable=False, unique=True)
    is_active: StatusEnum = Field(default=StatusEnum.ACTIVE)

    membership_id: int = Field(
        foreign_key="membership.id",
        nullable=False
    )
    membership: "Membership" = Relationship(back_populates="customers")

    attendances: list["Attendance"] = Relationship(back_populates="customer")
