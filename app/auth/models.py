from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String
from app.core.enums import RoleEnum, StatusEnum

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(
        sa_column=Column(String(255), unique=True, index=True, nullable=False)
    )

    hashed_password: str = Field(nullable=False)
    role: RoleEnum  # ADMIN | CUSTOMER
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)