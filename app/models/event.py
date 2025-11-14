"""Event-related database models."""

from typing import Any, Dict, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModel, TimestampMixin


class UserEvent(Base, BaseModel, TimestampMixin):
    """User event model for streaming.user_events table."""

    __tablename__ = "user_events"
    __table_args__ = {"schema": "streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, doc="Event ID")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("streaming.users.id", ondelete="CASCADE"),
        nullable=False,
        doc="User who triggered the event"
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="Type of event"
    )
    event_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, doc="Event payload data"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET, nullable=True, doc="User IP address"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="User agent string"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="events")

    @property
    def device_info(self) -> Dict[str, Any]:
        """Extract device information from event data."""
        if self.event_data:
            return {
                "device": self.event_data.get("device"),
                "browser": self.event_data.get("browser"),
                "os": self.event_data.get("os"),
                "screen_resolution": self.event_data.get("screen_resolution")
            }
        return {}

    def __str__(self) -> str:
        return f"{self.event_type} by user {self.user_id} at {self.created_at}"


class ProductView(Base, BaseModel, TimestampMixin):
    """Product view model for streaming.product_views table."""

    __tablename__ = "product_views"
    __table_args__ = {"schema": "streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, doc="View ID")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("streaming.users.id", ondelete="CASCADE"),
        nullable=False,
        doc="User who viewed the product"
    )
    product_id: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Product that was viewed"
    )
    product_category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, doc="Product category"
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="User session ID"
    )
    view_duration: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="View duration in seconds"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="product_views")

    @property
    def is_meaningful_view(self) -> bool:
        """Check if this is a meaningful view (>10 seconds)."""
        return self.view_duration is not None and self.view_duration > 10

    def __str__(self) -> str:
        duration_str = f" ({self.view_duration}s)" if self.view_duration else ""
        return f"Product {self.product_id} viewed by user {self.user_id}{duration_str}"


# Event type constants for better type safety
class EventTypes:
    """Common event types."""
    LOGIN = "login"
    LOGOUT = "logout"
    PRODUCT_VIEW = "product_view"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    PURCHASE = "purchase"
    SEARCH = "search"
    FILTER_APPLY = "filter_apply"
    PAGE_VIEW = "page_view"
    CLICK = "click"
    SCROLL = "scroll"
    FORM_SUBMIT = "form_submit"
    ERROR = "error"