from sqlmodel import SQLModel, Field
from typing import Optional
from app.core.enums import ProductType, StatusEnum

class ProductCreate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(min_length=1, max_length=255)

    product_type: ProductType

    stock: int = Field(ge=0)
    price: int = Field(ge=0)


class ProductRead(SQLModel):
    id: int

    name: str
    description: Optional[str]

    product_type: ProductType

    stock: int
    price: int

    status: StatusEnum

class ProductUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None,min_length=1, max_length=255)

    product_type: Optional[ProductType] = None
    stock: Optional[int] = Field(default=None, ge=0)

    price: Optional[int] = Field(default=None, ge=0)


