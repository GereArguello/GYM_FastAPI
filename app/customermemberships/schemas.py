from sqlmodel import SQLModel
from typing import Optional
from datetime import date
from app.core.enums import MembershipStatusEnum

class CustomerMembershipRead(SQLModel):
    id: int

    customer_id: int 
    membership_id: int 

    status: MembershipStatusEnum

    start_date: date 
    end_date: Optional[date]
