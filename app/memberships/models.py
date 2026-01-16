from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List



class Membership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    max_days_per_week: int | None
    points_multiplier: float
    is_active: bool = True

    customers: List["Customer"] = Relationship(back_populates="membership")