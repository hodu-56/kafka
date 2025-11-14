"""Kafka consumer implementations for different message types."""

import asyncio
from datetime import datetime
from typing import Any, Dict

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.models.event import EventTypes
from app.services.kafka_service import KafkaService

logger = structlog.get_logger(__name__)
settings = get_settings()


class StreamingMessageConsumer:
    """High-performance consumer for streaming messages."""

    def __init__(self, kafka_service: KafkaService):
        self.kafka_service = kafka_service
        self.processed_count = 0
        self.error_count = 0
        self.is_running = False

    async def start(self) -> None:
        """Start consuming messages from all streaming topics."""
        try:
            logger.info("Starting streaming message consumer")

            # Subscribe to all streaming topics
            await self._subscribe_to_topics()

            self.is_running = True
            logger.info("Streaming message consumer started successfully")

        except Exception as e:
            logger.error("Failed to start streaming message consumer", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop consuming messages."""
        self.is_running = False
        logger.info("Streaming message consumer stopped")

    async def _subscribe_to_topics(self) -> None:
        """Subscribe to all streaming topics."""
        topics_handlers = {
            "streaming.users": self._handle_user_event,
            "streaming.orders": self._handle_order_event,
            "streaming.order_items": self._handle_order_item_event,
            "streaming.user_events": self._handle_user_activity_event,
            "streaming.product_views": self._handle_product_view_event,
        }

        for topic, handler in topics_handlers.items():
            await self.kafka_service.subscribe_to_topic(
                topic=topic,
                message_handler=handler,
                consumer_group="streaming-processor"
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def _handle_user_event(self, message_data: Dict[str, Any]) -> None:
        """Handle user-related CDC events."""
        try:
            value = message_data["value"]
            operation = value.get("op")  # Debezium operation: c=create, u=update, d=delete

            if operation == "c":
                await self._process_user_created(value["after"])
            elif operation == "u":
                await self._process_user_updated(value["before"], value["after"])
            elif operation == "d":
                await self._process_user_deleted(value["before"])

        except Exception as e:
            self.error_count += 1
            logger.error("Error handling user event", error=str(e), message=message_data)
            raise

    async def _process_user_created(self, user_data: Dict[str, Any]) -> None:
        """Process user creation event."""
        try:
            logger.info("Processing user created event", user_id=user_data.get("id"))

            # Create welcome event
            welcome_event = {
                "user_id": user_data["id"],
                "event_type": EventTypes.REGISTER,
                "event_data": {
                    "welcome": True,
                    "registration_source": "web",
                    "user_agent": "system"
                },
                "timestamp": datetime.now().isoformat()
            }

            # Send to analytics stream
            await self._forward_to_analytics("user_created", {
                "user_id": user_data["id"],
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "timestamp": user_data.get("created_at")
            })

            self.processed_count += 1
            logger.debug("User created event processed", user_id=user_data.get("id"))

        except Exception as e:
            logger.error("Error processing user created event", error=str(e))
            raise

    async def _process_user_updated(self, before_data: Dict[str, Any], after_data: Dict[str, Any]) -> None:
        """Process user update event."""
        try:
            user_id = after_data.get("id")
            logger.debug("Processing user updated event", user_id=user_id)

            # Check what changed
            changes = {}
            for key in after_data:
                if before_data.get(key) != after_data.get(key):
                    changes[key] = {
                        "old": before_data.get(key),
                        "new": after_data.get(key)
                    }

            if changes:
                await self._forward_to_analytics("user_updated", {
                    "user_id": user_id,
                    "changes": changes,
                    "timestamp": after_data.get("updated_at")
                })

            self.processed_count += 1

        except Exception as e:
            logger.error("Error processing user updated event", error=str(e))
            raise

    async def _process_user_deleted(self, user_data: Dict[str, Any]) -> None:
        """Process user deletion event."""
        try:
            user_id = user_data.get("id")
            logger.info("Processing user deleted event", user_id=user_id)

            await self._forward_to_analytics("user_deleted", {
                "user_id": user_id,
                "username": user_data.get("username"),
                "timestamp": datetime.now().isoformat()
            })

            self.processed_count += 1

        except Exception as e:
            logger.error("Error processing user deleted event", error=str(e))
            raise

    async def _handle_order_event(self, message_data: Dict[str, Any]) -> None:
        """Handle order-related CDC events."""
        try:
            value = message_data["value"]
            operation = value.get("op")

            if operation == "c":
                await self._process_order_created(value["after"])
            elif operation == "u":
                await self._process_order_updated(value["before"], value["after"])

        except Exception as e:
            self.error_count += 1
            logger.error("Error handling order event", error=str(e), message=message_data)
            raise

    async def _process_order_created(self, order_data: Dict[str, Any]) -> None:
        """Process order creation event."""
        try:
            logger.info("Processing order created event", order_id=order_data.get("id"))

            # Forward to order analytics
            await self._forward_to_analytics("order_created", {
                "order_id": order_data["id"],
                "user_id": order_data["user_id"],
                "order_number": order_data["order_number"],
                "total_amount": float(order_data["total_amount"]),
                "status": order_data["status"],
                "timestamp": order_data.get("created_at")
            })

            self.processed_count += 1

        except Exception as e:
            logger.error("Error processing order created event", error=str(e))
            raise

    async def _process_order_updated(self, before_data: Dict[str, Any], after_data: Dict[str, Any]) -> None:
        """Process order update event."""
        try:
            order_id = after_data.get("id")
            logger.debug("Processing order updated event", order_id=order_id)

            # Check for status changes
            old_status = before_data.get("status")
            new_status = after_data.get("status")

            if old_status != new_status:
                await self._forward_to_analytics("order_status_changed", {
                    "order_id": order_id,
                    "user_id": after_data["user_id"],
                    "old_status": old_status,
                    "new_status": new_status,
                    "timestamp": after_data.get("updated_at")
                })

            self.processed_count += 1

        except Exception as e:
            logger.error("Error processing order updated event", error=str(e))
            raise

    async def _handle_order_item_event(self, message_data: Dict[str, Any]) -> None:
        """Handle order item CDC events."""
        try:
            value = message_data["value"]
            operation = value.get("op")

            if operation == "c":
                await self._process_order_item_added(value["after"])

        except Exception as e:
            self.error_count += 1
            logger.error("Error handling order item event", error=str(e))
            raise

    async def _process_order_item_added(self, item_data: Dict[str, Any]) -> None:
        """Process order item addition."""
        try:
            await self._forward_to_analytics("order_item_added", {
                "order_id": item_data["order_id"],
                "product_id": item_data["product_id"],
                "product_name": item_data["product_name"],
                "quantity": item_data["quantity"],
                "unit_price": float(item_data["unit_price"]),
                "timestamp": item_data.get("created_at")
            })

            self.processed_count += 1

        except Exception as e:
            logger.error("Error processing order item added event", error=str(e))
            raise

    async def _handle_user_activity_event(self, message_data: Dict[str, Any]) -> None:
        """Handle user activity events."""
        try:
            value = message_data["value"]
            operation = value.get("op")

            if operation == "c":
                await self._process_user_activity(value["after"])

        except Exception as e:
            self.error_count += 1
            logger.error("Error handling user activity event", error=str(e))
            raise

    async def _process_user_activity(self, event_data: Dict[str, Any]) -> None:
        """Process user activity event."""
        try:
            # Forward high-value events to real-time analytics
            high_value_events = [
                EventTypes.LOGIN,
                EventTypes.PURCHASE,
                EventTypes.ADD_TO_CART,
                EventTypes.SEARCH
            ]

            event_type = event_data.get("event_type")
            if event_type in high_value_events:
                await self._forward_to_analytics("high_value_event", {
                    "user_id": event_data["user_id"],
                    "event_type": event_type,
                    "event_data": event_data.get("event_data", {}),
                    "timestamp": event_data.get("created_at")
                })

            self.processed_count += 1

        except Exception as e:
            logger.error("Error processing user activity event", error=str(e))
            raise

    async def _handle_product_view_event(self, message_data: Dict[str, Any]) -> None:
        """Handle product view events."""
        try:
            value = message_data["value"]
            operation = value.get("op")

            if operation == "c":
                await self._process_product_view(value["after"])

        except Exception as e:
            self.error_count += 1
            logger.error("Error handling product view event", error=str(e))
            raise

    async def _process_product_view(self, view_data: Dict[str, Any]) -> None:
        """Process product view event."""
        try:
            # Forward to product analytics
            await self._forward_to_analytics("product_viewed", {
                "user_id": view_data["user_id"],
                "product_id": view_data["product_id"],
                "product_category": view_data.get("product_category"),
                "view_duration": view_data.get("view_duration"),
                "session_id": view_data.get("session_id"),
                "timestamp": view_data.get("created_at")
            })

            self.processed_count += 1

        except Exception as e:
            logger.error("Error processing product view event", error=str(e))
            raise

    async def _forward_to_analytics(self, event_type: str, data: Dict[str, Any]) -> None:
        """Forward processed events to analytics topics."""
        try:
            analytics_message = {
                "event_type": event_type,
                "data": data,
                "processed_at": datetime.now().isoformat(),
                "source": "streaming-processor"
            }

            # Route to appropriate analytics topic
            if event_type.startswith("user_"):
                topic = "analytics.users"
            elif event_type.startswith("order_"):
                topic = "analytics.orders"
            elif event_type.startswith("product_"):
                topic = "analytics.products"
            else:
                topic = "analytics.events"

            await self.kafka_service.produce_message(
                topic=topic,
                value=analytics_message,
                key=str(data.get("user_id", "unknown"))
            )

        except Exception as e:
            logger.error("Error forwarding to analytics", error=str(e), event_type=event_type)
            # Don't re-raise here to avoid breaking the main processing flow

    def get_metrics(self) -> Dict[str, Any]:
        """Get consumer metrics."""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "is_running": self.is_running,
            "error_rate": self.error_count / max(self.processed_count, 1)
        }