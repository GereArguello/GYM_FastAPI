from sqlmodel import SQLModel


class MembershipCreate(SQLModel):
    name: str
    max_days_per_week: int | None
    points_multiplier: float



class MembershipRead(SQLModel):
    id: int
    name: str
    max_days_per_week: int | None
    points_multiplier: float
    is_active: bool

class MembershipUpdate(SQLModel):
    name: str | None = None
    max_days_per_week: int | None = None
    points_multiplier: float| None = None
