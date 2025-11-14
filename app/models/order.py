"""Order-related database models."""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import DECIMAL, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModel, TimestampMixin


class Order(Base, BaseModel, TimestampMixin):
    """Order model for streaming.orders table."""

    __tablename__ = "orders"
    __table_args__ = {"schema": "streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, doc="Order ID")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("streaming.users.id", ondelete="CASCADE"),
        nullable=False,
        doc="User who placed the order"
    )
    order_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, doc="Unique order number"
    )
    total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, doc="Total order amount"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", doc="Order status"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    @property
    def item_count(self) -> int:
        """Get total number of items in order."""
        return sum(item.quantity for item in self.items)

    def __str__(self) -> str:
        return f"Order {self.order_number} - ${self.total_amount} ({self.status})"


class OrderItem(Base, BaseModel, TimestampMixin):
    """Order item model for streaming.order_items table."""

    __tablename__ = "order_items"
    __table_args__ = {"schema": "streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, doc="Order item ID")
    order_id: Mapped[int] = mapped_column(
        ForeignKey("streaming.orders.id", ondelete="CASCADE"),
        nullable=False,
        doc="Associated order ID"
    )
    product_id: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Product ID"
    )
    product_name: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="Product name"
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Item quantity"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, doc="Unit price"
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")

    @property
    def line_total(self) -> Decimal:
        """Calculate line total (quantity * unit_price)."""
        return self.quantity * self.unit_price

    def __str__(self) -> str:
        return f"{self.product_name} x{self.quantity} @ ${self.unit_price}"