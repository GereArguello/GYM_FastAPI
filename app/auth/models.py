from sqlmodel import SQLModel, Field
from app.core.enums import RoleEnum

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: RoleEnum  # ADMIN | CUSTOMER
    is_active: bool = True