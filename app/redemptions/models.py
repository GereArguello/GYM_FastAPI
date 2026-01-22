from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.customers.models import Customer
    from app.shop.models import Product



class Redemption(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    customer_id: int = Field(
        foreign_key="customer.id",
        nullable=False,
        index=True
    )

    product_id: int = Field(
        foreign_key="product.id",
        nullable=False,
        index=True
    )

    customer: "Customer" = Relationship(back_populates="redemptions")
    product: "Product" = Relationship(back_populates="redemptions")

    points_spent: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)

    product_name_snapshot: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )