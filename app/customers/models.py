from datetime import date
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from typing import Optional
from core.enums import StatusEnum


class CustomerBase(SQLModel):
    name: str
    birth_date: date
    email: EmailStr
    is_active: StatusEnum = Field(default=StatusEnum.ACTIVE)



class Customer(CustomerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    membership_id: int = Field(foreign_key="membership.id", nullable=False)
    membership: "Membership" = Relationship(back_populates="customers")

    attendances: list["Attendance"] = Relationship(back_populates="customer")
