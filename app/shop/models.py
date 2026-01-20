from sqlmodel import SQLModel, Field
from typing import Optional
from app.core.enums import ProductType

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(index=True,unique=True)
    description: Optional[str]
    
    product_type: ProductType

    stock: int
    price: int

    is_active: bool = Field(default=True)
