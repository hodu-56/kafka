"""User-related Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=50, description="User first name")
    last_name: Optional[str] = Field(None, max_length=50, description="User last name")
    is_active: bool = Field(True, description="Whether user is active")


class UserCreate(UserBase):
    """Schema for creating users."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating users."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class User(UserBase):
    """Schema for user responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    full_name: str = Field(..., description="User full name")


class UserWithStats(User):
    """User schema with statistics."""
    total_orders: int = Field(0, description="Total number of orders")
    total_spent: float = Field(0.0, description="Total amount spent")
    last_order_date: Optional[datetime] = Field(None, description="Last order date")
    event_count: int = Field(0, description="Total number of events")


class UserSummary(BaseModel):
    """Summary schema for user lists."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime