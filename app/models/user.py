"""User-related database models."""

from typing import List, Optional

from sqlalchemy import Boolean, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModel, TimestampMixin


class User(Base, BaseModel, TimestampMixin):
    """User model for streaming.users table."""

    __tablename__ = "users"
    __table_args__ = {"schema": "streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, doc="User ID")
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, doc="Unique username"
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, doc="User email address"
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, doc="User first name"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, doc="User last name"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, doc="Whether user is active"
    )

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    events: Mapped[List["UserEvent"]] = relationship(
        "UserEvent", back_populates="user", cascade="all, delete-orphan"
    )
    product_views: Mapped[List["ProductView"]] = relationship(
        "ProductView", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"