"""Event-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class UserEventBase(BaseModel):
    """Base user event schema."""
    event_type: str = Field(..., max_length=50, description="Type of event")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Event payload data")
    ip_address: Optional[IPvAnyAddress] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class UserEventCreate(UserEventBase):
    """Schema for creating user events."""
    user_id: int = Field(..., description="User who triggered the event")


class UserEvent(UserEventBase):
    """Schema for user event responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Event ID")
    user_id: int = Field(..., description="User who triggered the event")
    created_at: datetime = Field(..., description="Event creation timestamp")
    device_info: Dict[str, Any] = Field(..., description="Extracted device information")


class ProductViewBase(BaseModel):
    """Base product view schema."""
    product_id: int = Field(..., description="Product that was viewed")
    product_category: Optional[str] = Field(None, max_length=50, description="Product category")
    session_id: Optional[str] = Field(None, max_length=100, description="User session ID")
    view_duration: Optional[int] = Field(None, ge=0, description="View duration in seconds")


class ProductViewCreate(ProductViewBase):
    """Schema for creating product views."""
    user_id: int = Field(..., description="User who viewed the product")


class ProductView(ProductViewBase):
    """Schema for product view responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="View ID")
    user_id: int = Field(..., description="User who viewed the product")
    is_meaningful_view: bool = Field(..., description="Whether this is a meaningful view (>10s)")
    created_at: datetime = Field(..., description="View creation timestamp")


class EventAnalytics(BaseModel):
    """Event analytics schema."""
    event_type: str = Field(..., description="Event type")
    count: int = Field(..., description="Event count")
    unique_users: int = Field(..., description="Number of unique users")
    avg_per_user: float = Field(..., description="Average events per user")
    time_period: str = Field(..., description="Time period for analytics")


class SessionAnalytics(BaseModel):
    """Session analytics schema."""
    session_id: str = Field(..., description="Session ID")
    user_id: int = Field(..., description="User ID")
    start_time: datetime = Field(..., description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    duration_seconds: Optional[int] = Field(None, description="Session duration in seconds")
    page_views: int = Field(0, description="Number of page views")
    events_count: int = Field(0, description="Total number of events")
    conversion_events: int = Field(0, description="Number of conversion events")


class RealTimeEvent(BaseModel):
    """Real-time event schema for streaming."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    user_id: int = Field(..., description="User who triggered the event")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EventBatch(BaseModel):
    """Batch of events for processing."""
    batch_id: str = Field(..., description="Unique batch identifier")
    events: List[RealTimeEvent] = Field(..., description="List of events in batch")
    batch_size: int = Field(..., description="Number of events in batch")
    created_at: datetime = Field(..., description="Batch creation timestamp")


# Event type constants
class EventTypes:
    """Event type constants."""
    # User actions
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"

    # Product interactions
    PRODUCT_VIEW = "product_view"
    PRODUCT_SEARCH = "product_search"
    CATEGORY_VIEW = "category_view"

    # Shopping cart
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    CART_VIEW = "cart_view"

    # Purchase flow
    CHECKOUT_START = "checkout_start"
    PAYMENT_INFO = "payment_info"
    PURCHASE = "purchase"

    # Navigation
    PAGE_VIEW = "page_view"
    CLICK = "click"
    SCROLL = "scroll"

    # Forms
    FORM_START = "form_start"
    FORM_SUBMIT = "form_submit"
    FORM_ERROR = "form_error"

    # System
    ERROR = "error"
    API_CALL = "api_call"
    SYSTEM_EVENT = "system_event"