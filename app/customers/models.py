from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from app.core.enums import StatusEnum

# SOLO PARA IDE, EVITA IMPORTS CIRCULARES
if TYPE_CHECKING:
    from memberships.models import Membership
    from attendances.models import Attendance


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    first_name: str
    last_name: str
    birth_date: date
    email: EmailStr = Field(nullable=False, unique=True)
    is_active: StatusEnum = Field(default=StatusEnum.ACTIVE)

    attendances: list["Attendance"] = Relationship(back_populates="customer")
    memberships: list["CustomerMembership"] = Relationship(back_populates="customer")



class CustomerMembership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    customer_id: int = Field(foreign_key="customer.id")
    membership_id: int = Field(foreign_key="membership.id")

    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    is_active: bool = Field(default=True)

    customer: "Customer" = Relationship(back_populates="memberships")
    membership: "Membership" = Relationship(back_populates="customer_memberships")


