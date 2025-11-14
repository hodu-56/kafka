"""Order-related Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderItemBase(BaseModel):
    """Base order item schema."""
    product_id: int = Field(..., description="Product ID")
    product_name: str = Field(..., max_length=100, description="Product name")
    quantity: int = Field(..., gt=0, description="Item quantity")
    unit_price: Decimal = Field(..., gt=0, description="Unit price")


class OrderItemCreate(OrderItemBase):
    """Schema for creating order items."""
    pass


class OrderItem(OrderItemBase):
    """Schema for order item responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Order item ID")
    order_id: int = Field(..., description="Associated order ID")
    line_total: Decimal = Field(..., description="Line total (quantity * unit_price)")
    created_at: datetime = Field(..., description="Item creation timestamp")


class OrderBase(BaseModel):
    """Base order schema."""
    order_number: str = Field(..., max_length=50, description="Unique order number")
    status: str = Field(default="pending", max_length=20, description="Order status")


class OrderCreate(OrderBase):
    """Schema for creating orders."""
    user_id: int = Field(..., description="User who placed the order")
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Order items")


class OrderUpdate(BaseModel):
    """Schema for updating orders."""
    status: Optional[str] = Field(None, max_length=20)


class Order(OrderBase):
    """Schema for order responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Order ID")
    user_id: int = Field(..., description="User who placed the order")
    total_amount: Decimal = Field(..., description="Total order amount")
    item_count: int = Field(..., description="Total number of items")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_at: datetime = Field(..., description="Order last update timestamp")


class OrderWithItems(Order):
    """Order schema with items."""
    items: List[OrderItem] = Field(..., description="Order items")


class OrderWithUser(Order):
    """Order schema with user information."""
    from app.schemas.user import UserSummary
    user: UserSummary = Field(..., description="User who placed the order")


class OrderSummary(BaseModel):
    """Summary schema for order lists."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    user_id: int
    total_amount: Decimal
    status: str
    item_count: int
    created_at: datetime


# Order status constants
class OrderStatus:
    """Order status constants."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"