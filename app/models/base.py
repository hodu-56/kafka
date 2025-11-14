"""Base model classes and mixins."""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TimestampMixin:
    """Mixin for timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        doc="Record creation timestamp"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
        doc="Record last update timestamp"
    )


class BaseModel:
    """Base model with common functionality."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of model."""
        class_name = self.__class__.__name__
        attrs = []

        # Add primary key columns first
        for column in self.__table__.primary_key.columns:
            value = getattr(self, column.name)
            attrs.append(f"{column.name}={value!r}")

        # Add other important columns (like name, email, etc.)
        important_columns = ['name', 'username', 'email', 'title', 'status']
        for column_name in important_columns:
            if hasattr(self, column_name) and column_name not in [c.name for c in self.__table__.primary_key.columns]:
                value = getattr(self, column_name)
                attrs.append(f"{column_name}={value!r}")

        attrs_str = ", ".join(attrs)
        return f"{class_name}({attrs_str})"