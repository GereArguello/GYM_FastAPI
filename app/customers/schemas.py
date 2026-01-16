from datetime import date
from sqlmodel import SQLModel
from pydantic import EmailStr
from app.core.enums import StatusEnum


class CustomerCreate(SQLModel):
    name: str
    birth_date: date
    email: EmailStr
    membership_id: int


class CustomerRead(SQLModel):
    id: int
    first_name: str
    last_name: str
    birth_date: date
    email: EmailStr
    membership_id: int
    is_active: StatusEnum

class CustomerUpdate(SQLModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | None = None
    email: EmailStr | None = None
    membership_id: int | None = None

    model_config = {
        "extra": "forbid"
    }

