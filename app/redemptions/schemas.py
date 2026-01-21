from sqlmodel import SQLModel
from datetime import datetime

class RedemptionCreate(SQLModel):
    product_id: int
    quantity: int

class RedemptionRead(SQLModel):
    id: int
    customer_id: int
    product_id: int
    points_spent: int
    quantity: int
    product_name_snapshot: str
    created_at: datetime