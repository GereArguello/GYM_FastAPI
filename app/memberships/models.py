from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from customers.models import Customer

class Membership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    max_days_per_week: int | None
    points_multiplier: float
    is_active: bool = True

    customers: List["Customer"] = Relationship(back_populates="membership")