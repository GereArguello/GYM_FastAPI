from sqlmodel import SQLModel
from typing import Optional
from pydantic import EmailStr
from datetime import date
from app.core.enums import StatusEnum


class CustomerCreate(SQLModel):
    first_name: str
    last_name: str
    birth_date: date
    email: EmailStr
    password: str



class CustomerRead(SQLModel):
    id: int
    first_name: str
    last_name: str
    birth_date: date
    points_balance: int
    is_active: StatusEnum

class CustomerUpdate(SQLModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | None = None

    model_config = {
        "extra": "forbid"
    }

class CustomerMembershipRead(SQLModel):
    id: int

    customer_id: int 
    membership_id: int 

    start_date: date 
    end_date: Optional[date]
    is_active: bool 
