from sqlmodel import SQLModel
from typing import Optional
from app.core.enums import ProductType

class ProductCreate(SQLModel):
    name: str
    description: Optional[str]

    product_type: ProductType

    stock: int
    price: int


class ProductRead(SQLModel):
    id: int

    name: str
    description: Optional[str]

    product_type: ProductType

    stock: int
    price: int

    is_active: bool

class ProductUpdate(SQLModel):
    name: str | None = None
    description: Optional[str] | None = None

    product_type: ProductType | None = None
    stock: int | None = None

    price: int | None = None


