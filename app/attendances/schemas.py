from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime


class AttendanceCreate(SQLModel):
    customer_id : int 
    membership_id : Optional[int]
    

class AttendanceRead(SQLModel):
    id : int
    customer_id : int
    membership_id : Optional[int]
    check_in : datetime
    check_out : Optional[datetime]
    duration_minutes : Optional[int]
    points_awarded : Optional[int]
    is_valid : bool

