from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from customers.models import CustomerMembership
    from attendances.models import Attendance

class Membership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field (index=True, unique=True)
    max_days_per_week: int | None
    points_multiplier: float = Field(gt=0)
    is_active: bool = True

    customer_memberships: List["CustomerMembership"] = Relationship(back_populates="membership")
    attendances: List["Attendance"] = Relationship(back_populates="membership")