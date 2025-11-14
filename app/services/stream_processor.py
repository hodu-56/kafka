"""Stream processor for handling large-scale streaming data processing."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
import statistics
import time

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.kafka_service import KafkaService
from app.services.kinesis_service import KinesisService

logger = structlog.get_logger(__name__)
settings = get_settings()


class StreamProcessor:
    """High-performance stream processor for real-time data processing."""

    def __init__(self, kafka_service: KafkaService, kinesis_service: KinesisService):
        self.kafka_service = kafka_service
        self.kinesis_service = kinesis_service
        self.is_running = False
        self._processing_tasks: List[asyncio.Task] = []
        self._processors: Dict[str, Callable] = {}
        self._metrics_buffer: List[Dict[str, Any]] = []
        self._processing_stats = {
            "messages_processed": 0,
            "processing_errors": 0,
            "avg_processing_time": 0.0,
            "messages_per_second": 0.0,
            "last_reset": datetime.now()
        }

        # Performance tracking
        self._processing_times: List[float] = []
        self._last_metrics_flush = time.time()

    async def start_processing(self) -> None:
        """Start the stream processing pipeline."""
        try:
            logger.info("Starting stream processor")

            # Register default message processors
            self._register_default_processors()

            # Start consuming from configured topics
            await self._start_consumers()

            # Start metrics collection task
            metrics_task = asyncio.create_task(self._collect_metrics())
            self._processing_tasks.append(metrics_task)

            # Start cross-platform streaming (Kafka to Kinesis and vice versa)
            if settings.enable_cross_platform_streaming:
                cross_stream_task = asyncio.create_task(self._cross_platform_streaming())
                self._processing_tasks.append(cross_stream_task)

            self.is_running = True
            logger.info("Stream processor started successfully")

        except Exception as e:
            logger.error("Failed to start stream processor", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop the stream processing pipeline."""
        try:
            logger.info("Stopping stream processor")

            # Cancel all processing tasks
            for task in self._processing_tasks:
                task.cancel()

            await asyncio.gather(*self._processing_tasks, return_exceptions=True)
            self._processing_tasks.clear()

            self.is_running = False
            logger.info("Stream processor stopped")

        except Exception as e:
            logger.error("Error stopping stream processor", error=str(e))

    def register_processor(self, topic: str, processor: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Register a custom message processor for a specific topic."""
        self._processors[topic] = processor
        logger.info("Registered custom processor", topic=topic)

    async def _start_consumers(self) -> None:
        """Start consuming from configured Kafka topics."""
        try:
            # Subscribe to configured topics
            for topic in settings.kafka_topics_to_consume:
                await self.kafka_service.subscribe_to_topic(
                    topic=topic,
                    message_handler=self._process_message,
                    consumer_group=settings.kafka_consumer_group_id
                )

            logger.info(
                "Started consuming from topics",
                topics=settings.kafka_topics_to_consume
            )

        except Exception as e:
            logger.error("Failed to start consumers", error=str(e))
            raise

    async def _process_message(self, message_data: Dict[str, Any]) -> None:
        """Process a single message from Kafka."""
        start_time = time.time()

        try:
            topic = message_data.get("topic")
            value = message_data.get("value", {})

            logger.debug("Processing message", topic=topic, offset=message_data.get("offset"))

            # Apply topic-specific processor if available
            if topic in self._processors:
                processed_data = await self._processors[topic](value)
            else:
                processed_data = await self._default_processor(value)

            # Handle processed data based on configuration
            await self._handle_processed_data(topic, processed_data, message_data)

            # Track processing time
            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)

            # Keep only last 1000 processing times for performance
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-1000:]

            self._processing_stats["messages_processed"] += 1

            logger.debug(
                "Message processed successfully",
                topic=topic,
                processing_time=processing_time,
                offset=message_data.get("offset")
            )

        except Exception as e:
            self._processing_stats["processing_errors"] += 1
            logger.error(
                "Error processing message",
                error=str(e),
                topic=message_data.get("topic"),
                offset=message_data.get("offset")
            )

    async def _handle_processed_data(
        self,
        original_topic: str,
        processed_data: Dict[str, Any],
        original_message: Dict[str, Any]
    ) -> None:
        """Handle processed data by routing to appropriate destinations."""
        try:
            # Add metadata
            processed_data.update({
                "processed_at": datetime.now().isoformat(),
                "original_topic": original_topic,
                "original_offset": original_message.get("offset"),
                "original_partition": original_message.get("partition")
            })

            # Route to destination based on configuration
            if settings.enable_kafka_output:
                output_topic = f"{original_topic}_processed"
                await self.kafka_service.produce_message(
                    topic=output_topic,
                    value=processed_data,
                    key=original_message.get("key")
                )

            if settings.enable_kinesis_output:
                stream_name = f"{original_topic}-processed"
                await self.kinesis_service.put_record(
                    stream_name=stream_name,
                    data=processed_data,
                    partition_key=original_message.get("key") or str(processed_data.get("id", ""))
                )

            # Store in metrics buffer for analytics
            self._metrics_buffer.append({
                "timestamp": datetime.now().isoformat(),
                "topic": original_topic,
                "message_size": len(json.dumps(processed_data)),
                "processing_metadata": {
                    "original_partition": original_message.get("partition"),
                    "original_offset": original_message.get("offset")
                }
            })

        except Exception as e:
            logger.error("Failed to handle processed data", error=str(e), topic=original_topic)
            raise

    async def _default_processor(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Default message processor that adds enrichment and validation."""
        try:
            # Add processing metadata
            processed_data = data.copy()
            processed_data.update({
                "processor_id": "default",
                "enriched_at": datetime.now().isoformat(),
                "processing_version": "1.0"
            })

            # Validate required fields
            if "timestamp" not in processed_data:
                processed_data["timestamp"] = datetime.now().isoformat()

            # Add calculated fields based on data type
            if "event_type" in processed_data:
                processed_data["event_category"] = self._categorize_event(processed_data["event_type"])

            if "amount" in processed_data and isinstance(processed_data["amount"], (int, float)):
                processed_data["amount_category"] = self._categorize_amount(processed_data["amount"])

            # Add session information if user_id present
            if "user_id" in processed_data:
                processed_data["session_info"] = await self._get_session_info(processed_data["user_id"])

            return processed_data

        except Exception as e:
            logger.error("Error in default processor", error=str(e))
            # Return original data if processing fails
            return data

    def _categorize_event(self, event_type: str) -> str:
        """Categorize event types."""
        event_categories = {
            "user_login": "authentication",
            "user_logout": "authentication",
            "password_reset": "authentication",
            "purchase": "transaction",
            "refund": "transaction",
            "payment": "transaction",
            "page_view": "analytics",
            "click": "analytics",
            "search": "analytics",
            "error": "system",
            "warning": "system"
        }
        return event_categories.get(event_type.lower(), "other")

    def _categorize_amount(self, amount: float) -> str:
        """Categorize transaction amounts."""
        if amount < 10:
            return "micro"
        elif amount < 100:
            return "small"
        elif amount < 1000:
            return "medium"
        elif amount < 10000:
            return "large"
        else:
            return "enterprise"

    async def _get_session_info(self, user_id: str) -> Dict[str, Any]:
        """Get session information for a user (mock implementation)."""
        # In a real implementation, this would query a session store or database
        return {
            "session_id": f"session_{user_id}_{int(time.time())}",
            "session_start": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "device_type": "web",
            "location": "unknown"
        }

    def _register_default_processors(self) -> None:
        """Register default processors for common data types."""

        async def order_processor(data: Dict[str, Any]) -> Dict[str, Any]:
            """Process order events."""
            processed = data.copy()

            # Calculate order metrics
            if "items" in processed and isinstance(processed["items"], list):
                processed["item_count"] = len(processed["items"])
                processed["total_quantity"] = sum(item.get("quantity", 0) for item in processed["items"])

            # Add order classification
            if "total_amount" in processed:
                processed["order_size_category"] = self._categorize_amount(processed["total_amount"])

            processed["processed_by"] = "order_processor"
            return processed

        async def user_processor(data: Dict[str, Any]) -> Dict[str, Any]:
            """Process user events."""
            processed = data.copy()

            # Add user segmentation
            if "user_id" in processed:
                processed["user_segment"] = await self._determine_user_segment(processed["user_id"])

            # Anonymize sensitive data
            if "email" in processed:
                processed["email_domain"] = processed["email"].split("@")[-1]
                del processed["email"]  # Remove sensitive data

            processed["processed_by"] = "user_processor"
            return processed

        async def event_processor(data: Dict[str, Any]) -> Dict[str, Any]:
            """Process general events."""
            processed = data.copy()

            # Add event metrics
            processed["event_id"] = f"evt_{int(time.time() * 1000000)}"
            processed["processing_latency"] = 0  # Would calculate actual latency

            # Add geolocation if IP present (mock)
            if "ip_address" in processed:
                processed["geo_location"] = await self._get_geo_location(processed["ip_address"])

            processed["processed_by"] = "event_processor"
            return processed

        # Register processors
        self._processors["orders"] = order_processor
        self._processors["users"] = user_processor
        self._processors["events"] = event_processor

    async def _determine_user_segment(self, user_id: str) -> str:
        """Determine user segment (mock implementation)."""
        # In a real implementation, this would query user data
        hash_val = hash(user_id) % 4
        segments = ["bronze", "silver", "gold", "platinum"]
        return segments[hash_val]

    async def _get_geo_location(self, ip_address: str) -> Dict[str, str]:
        """Get geo location from IP (mock implementation)."""
        # In a real implementation, this would use a GeoIP service
        return {
            "country": "US",
            "region": "CA",
            "city": "San Francisco"
        }

    async def _collect_metrics(self) -> None:
        """Collect and report processing metrics."""
        while self.is_running:
            try:
                await asyncio.sleep(settings.metrics_collection_interval)

                # Calculate metrics
                current_time = time.time()
                time_diff = current_time - self._last_metrics_flush

                if self._processing_times:
                    avg_processing_time = statistics.mean(self._processing_times)
                    self._processing_stats["avg_processing_time"] = avg_processing_time

                messages_per_second = self._processing_stats["messages_processed"] / time_diff if time_diff > 0 else 0
                self._processing_stats["messages_per_second"] = messages_per_second

                logger.info(
                    "Processing metrics",
                    messages_processed=self._processing_stats["messages_processed"],
                    processing_errors=self._processing_stats["processing_errors"],
                    avg_processing_time=self._processing_stats["avg_processing_time"],
                    messages_per_second=messages_per_second,
                    buffer_size=len(self._metrics_buffer)
                )

                # Flush metrics buffer if too large
                if len(self._metrics_buffer) > settings.metrics_buffer_size:
                    await self._flush_metrics_buffer()

                # Reset counters
                self._processing_stats["messages_processed"] = 0
                self._processing_stats["processing_errors"] = 0
                self._last_metrics_flush = current_time

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error collecting metrics", error=str(e))

    async def _flush_metrics_buffer(self) -> None:
        """Flush metrics buffer to persistent storage."""
        try:
            if not self._metrics_buffer:
                return

            # In a real implementation, this would save to database or analytics platform
            logger.info(
                "Flushing metrics buffer",
                buffer_size=len(self._metrics_buffer),
                first_timestamp=self._metrics_buffer[0]["timestamp"] if self._metrics_buffer else None,
                last_timestamp=self._metrics_buffer[-1]["timestamp"] if self._metrics_buffer else None
            )

            # Send to Kafka for analytics if enabled
            if settings.enable_metrics_to_kafka:
                await self.kafka_service.produce_message(
                    topic="processing_metrics",
                    value={
                        "metrics": self._metrics_buffer,
                        "flushed_at": datetime.now().isoformat(),
                        "count": len(self._metrics_buffer)
                    }
                )

            # Clear buffer
            self._metrics_buffer.clear()

        except Exception as e:
            logger.error("Failed to flush metrics buffer", error=str(e))

    async def _cross_platform_streaming(self) -> None:
        """Handle cross-platform streaming between Kafka and Kinesis."""
        while self.is_running:
            try:
                await asyncio.sleep(settings.cross_platform_sync_interval)

                # This is a simplified implementation
                # In a real scenario, you might want to:
                # 1. Stream high-volume data from Kafka to Kinesis for AWS analytics
                # 2. Stream processed results from Kinesis back to Kafka
                # 3. Implement data format conversions
                # 4. Handle schema evolution

                logger.debug("Cross-platform streaming cycle completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cross-platform streaming", error=str(e))

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return {
            **self._processing_stats,
            "is_running": self.is_running,
            "active_processors": len(self._processors),
            "metrics_buffer_size": len(self._metrics_buffer),
            "active_tasks": len(self._processing_tasks)
        }

    async def is_healthy(self) -> bool:
        """Check if stream processor is healthy."""
        try:
            # Check if services are healthy
            kafka_healthy = await self.kafka_service.is_healthy()
            kinesis_healthy = await self.kinesis_service.is_healthy()

            # Check if processing is working (no errors in last minute)
            recent_errors = self._processing_stats["processing_errors"]

            return (
                self.is_running and
                kafka_healthy and
                kinesis_healthy and
                recent_errors < settings.max_allowed_processing_errors
            )

        except Exception as e:
            logger.debug("Stream processor health check failed", error=str(e))
            return False