from sqlmodel import SQLModel, Field
from typing import Optional
from app.core.enums import StatusEnum


class MembershipCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    max_days_per_week: int = Field(ge=1)
    points_multiplier: float = Field(ge=1)



class MembershipRead(SQLModel):
    id: int
    name: str
    max_days_per_week: int
    points_multiplier: float
    status: StatusEnum

class MembershipUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    max_days_per_week: Optional[int] = Field(default=None, ge=1)
    points_multiplier: Optional[float] = Field(default=None, ge=1)
