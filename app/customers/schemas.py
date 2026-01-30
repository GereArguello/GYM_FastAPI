from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import EmailStr
from datetime import date
from app.core.enums import StatusEnum, MembershipStatusEnum


class CustomerCreate(SQLModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    birth_date: date
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)



class CustomerRead(SQLModel):
    id: int
    first_name: str
    last_name: str
    birth_date: date
    points_balance: int
    status: StatusEnum

class CustomerUpdate(SQLModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100) 
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    birth_date: Optional[date] = None

    model_config = {
        "extra": "forbid"
    }

class CustomerMembershipRead(SQLModel):
    id: int

    customer_id: int 
    membership_id: int 

    status: MembershipStatusEnum

    start_date: date 
    end_date: Optional[date]


