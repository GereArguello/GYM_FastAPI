from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from app.core.enums import ProductType


if TYPE_CHECKING:
    from redemptions.models import Redemption


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(index=True,unique=True)
    description: Optional[str]
    
    product_type: ProductType

    stock: int = Field(ge=0)
    price: int = Field(ge=0)

    is_active: bool = Field(default=True)

    redemptions : list["Redemption"] = Relationship(back_populates="product")

