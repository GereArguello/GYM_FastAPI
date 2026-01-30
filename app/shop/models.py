from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String
from typing import Optional, TYPE_CHECKING
from app.core.enums import ProductType, StatusEnum


if TYPE_CHECKING:
    from redemptions.models import Redemption


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(
        sa_column=Column(String(150), index=True, unique=True, nullable=False)
    )

    description: Optional[str] = Field(
        sa_column=Column(String(255))
    )

    product_type: ProductType

    stock: int = Field(ge=0)
    price: int = Field(ge=0)

    status: StatusEnum = Field(default=StatusEnum.ACTIVE)

    redemptions: list["Redemption"] = Relationship(back_populates="product")

