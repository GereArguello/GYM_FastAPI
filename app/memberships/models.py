from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String
from typing import Optional, List, TYPE_CHECKING
from app.core.enums import StatusEnum

if TYPE_CHECKING:
    from app.customers.models import CustomerMembership

class Membership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(
        sa_column=Column(String(100),index=True, unique=True, nullable=False)
        )
    
    max_days_per_week: int = Field(ge=1)

    points_multiplier: float = Field(ge=1)

    status: StatusEnum = Field(default=StatusEnum.ACTIVE)

    customer_memberships: List["CustomerMembership"] = Relationship(back_populates="membership")
