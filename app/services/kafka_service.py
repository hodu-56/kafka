"""Kafka service for producing and consuming messages."""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from kafka import KafkaAdminClient
from kafka.admin import ConfigResource, ConfigResourceType, NewTopic
from kafka.errors import TopicAlreadyExistsError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class KafkaService:
    """Kafka service for high-performance message production and consumption."""

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.admin_client: Optional[KafkaAdminClient] = None
        self.is_running = False
        self._consumer_tasks: Dict[str, asyncio.Task] = {}
        self._message_handlers: Dict[str, Callable] = {}

        # Metrics tracking
        self.produced_count = 0
        self.consumed_count = 0
        self.error_count = 0

    async def start(self) -> None:
        """Start Kafka service."""
        try:
            logger.info("Starting Kafka service")

            # Initialize admin client
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=settings.kafka_servers_list,
                client_id="streaming-admin"
            )

            # Initialize producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_servers_list,
                client_id="streaming-producer",
                value_serializer=self._serialize_message,
                key_serializer=self._serialize_key,
                compression_type="gzip",
                linger_ms=10,
                max_request_size=1048576,
                request_timeout_ms=30000,
                enable_idempotence=True,
            )

            await self.producer.start()
            self.is_running = True

            logger.info("Kafka service started successfully")

        except Exception as e:
            logger.error("Failed to start Kafka service", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop Kafka service."""
        try:
            logger.info("Stopping Kafka service")

            # Stop all consumer tasks
            for task in self._consumer_tasks.values():
                task.cancel()

            await asyncio.gather(*self._consumer_tasks.values(), return_exceptions=True)
            self._consumer_tasks.clear()

            # Stop all consumers
            for consumer in self.consumers.values():
                await consumer.stop()
            self.consumers.clear()

            # Stop producer
            if self.producer:
                await self.producer.stop()

            # Close admin client
            if self.admin_client:
                self.admin_client.close()

            self.is_running = False
            logger.info("Kafka service stopped")

        except Exception as e:
            logger.error("Error stopping Kafka service", error=str(e))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def produce_message(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        partition: Optional[int] = None
    ) -> Dict[str, Any]:
        """Produce a message to Kafka topic."""
        if not self.producer or not self.is_running:
            raise RuntimeError("Kafka service not started")

        try:
            # Add timestamp if not present
            if "timestamp" not in value:
                value["timestamp"] = datetime.now().isoformat()

            # Prepare headers
            kafka_headers = []
            if headers:
                kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]

            # Add correlation ID
            correlation_id = f"msg-{datetime.now().timestamp()}"
            kafka_headers.append(("correlation_id", correlation_id.encode('utf-8')))

            # Send message
            record_metadata = await self.producer.send_and_wait(
                topic=topic,
                value=value,
                key=key,
                headers=kafka_headers,
                partition=partition
            )

            self.produced_count += 1

            result = {
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset,
                "timestamp": record_metadata.timestamp,
                "message_id": correlation_id
            }

            logger.debug(
                "Message produced successfully",
                topic=topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset
            )

            return result

        except KafkaError as e:
            self.error_count += 1
            logger.error("Failed to produce message", error=str(e), topic=topic)
            raise
        except Exception as e:
            self.error_count += 1
            logger.error("Unexpected error producing message", error=str(e), topic=topic)
            raise

    async def batch_produce(
        self,
        messages: List[Dict[str, Any]],
        topic: str
    ) -> List[Dict[str, Any]]:
        """Produce multiple messages in batch."""
        if not self.producer or not self.is_running:
            raise RuntimeError("Kafka service not started")

        try:
            tasks = []
            for msg in messages:
                task = self.produce_message(
                    topic=topic,
                    value=msg.get("value", {}),
                    key=msg.get("key"),
                    headers=msg.get("headers"),
                    partition=msg.get("partition")
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "Failed to produce batch message",
                        error=str(result),
                        message_index=i
                    )
                else:
                    successful_results.append(result)

            logger.info(
                "Batch produce completed",
                total_messages=len(messages),
                successful=len(successful_results),
                failed=len(messages) - len(successful_results)
            )

            return successful_results

        except Exception as e:
            logger.error("Failed to batch produce messages", error=str(e))
            raise

    async def subscribe_to_topic(
        self,
        topic: str,
        message_handler: Callable[[Dict[str, Any]], None],
        consumer_group: Optional[str] = None
    ) -> None:
        """Subscribe to a topic and process messages."""
        if topic in self.consumers:
            logger.warning("Already subscribed to topic", topic=topic)
            return

        try:
            # Create consumer
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=settings.kafka_servers_list,
                group_id=consumer_group or settings.kafka_consumer_group_id,
                client_id=f"streaming-consumer-{topic}",
                auto_offset_reset=settings.kafka_auto_offset_reset,
                enable_auto_commit=settings.kafka_enable_auto_commit,
                max_poll_records=settings.kafka_max_poll_records,
                value_deserializer=self._deserialize_message,
                key_deserializer=self._deserialize_key,
                session_timeout_ms=30000,
                heartbeat_interval_ms=3000,
            )

            await consumer.start()
            self.consumers[topic] = consumer
            self._message_handlers[topic] = message_handler

            # Start consumer task
            consumer_task = asyncio.create_task(
                self._consume_messages(topic, consumer, message_handler)
            )
            self._consumer_tasks[topic] = consumer_task

            logger.info(
                "Subscribed to topic",
                topic=topic,
                consumer_group=consumer_group or settings.kafka_consumer_group_id
            )

        except Exception as e:
            logger.error("Failed to subscribe to topic", error=str(e), topic=topic)
            raise

    async def _consume_messages(
        self,
        topic: str,
        consumer: AIOKafkaConsumer,
        message_handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Consume messages from topic."""
        try:
            async for message in consumer:
                try:
                    # Process message
                    message_data = {
                        "topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                        "key": message.key,
                        "value": message.value,
                        "timestamp": message.timestamp,
                        "headers": dict(message.headers) if message.headers else {}
                    }

                    await message_handler(message_data)
                    self.consumed_count += 1

                    logger.debug(
                        "Message processed successfully",
                        topic=topic,
                        partition=message.partition,
                        offset=message.offset
                    )

                except Exception as e:
                    self.error_count += 1
                    logger.error(
                        "Error processing message",
                        error=str(e),
                        topic=topic,
                        partition=message.partition,
                        offset=message.offset
                    )

        except asyncio.CancelledError:
            logger.info("Consumer task cancelled", topic=topic)
        except Exception as e:
            logger.error("Consumer error", error=str(e), topic=topic)

    async def create_topic(
        self,
        topic_name: str,
        partitions: int = 3,
        replication_factor: int = 1,
        config: Optional[Dict[str, str]] = None
    ) -> None:
        """Create a new Kafka topic."""
        if not self.admin_client:
            raise RuntimeError("Admin client not initialized")

        try:
            topic_config = config or {
                "cleanup.policy": "delete",
                "retention.ms": "604800000",  # 7 days
                "compression.type": "gzip"
            }

            topic = NewTopic(
                name=topic_name,
                num_partitions=partitions,
                replication_factor=replication_factor,
                topic_configs=topic_config
            )

            result = self.admin_client.create_topics([topic])

            # Wait for topic creation
            for topic_name, future in result.items():
                try:
                    future.result()  # This will raise an exception if creation failed
                    logger.info(
                        "Topic created successfully",
                        topic=topic_name,
                        partitions=partitions,
                        replication_factor=replication_factor
                    )
                except TopicAlreadyExistsError:
                    logger.info("Topic already exists", topic=topic_name)
                except Exception as e:
                    logger.error("Failed to create topic", error=str(e), topic=topic_name)
                    raise

        except Exception as e:
            logger.error("Failed to create topic", error=str(e), topic=topic_name)
            raise

    async def delete_topic(self, topic_name: str) -> None:
        """Delete a Kafka topic."""
        if not self.admin_client:
            raise RuntimeError("Admin client not initialized")

        try:
            # Stop consumer if exists
            if topic_name in self.consumers:
                await self.unsubscribe_from_topic(topic_name)

            # Delete topic
            result = self.admin_client.delete_topics([topic_name])

            for topic, future in result.items():
                try:
                    future.result()
                    logger.info("Topic deleted successfully", topic=topic)
                except Exception as e:
                    logger.error("Failed to delete topic", error=str(e), topic=topic)
                    raise

        except Exception as e:
            logger.error("Failed to delete topic", error=str(e), topic=topic_name)
            raise

    async def list_topics(self) -> List[Dict[str, Any]]:
        """List all Kafka topics."""
        if not self.admin_client:
            raise RuntimeError("Admin client not initialized")

        try:
            metadata = self.admin_client.describe_topics()
            topics = []

            for topic_name, topic_metadata in metadata.items():
                topics.append({
                    "name": topic_name,
                    "partitions": len(topic_metadata.partitions),
                    "replication_factor": len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 0,
                    "config": {}  # Would need separate call to get configs
                })

            return topics

        except Exception as e:
            logger.error("Failed to list topics", error=str(e))
            raise

    async def list_consumer_groups(self) -> List[Dict[str, Any]]:
        """List all consumer groups."""
        # This would require additional implementation
        # For now, return mock data
        return [
            {
                "group_id": settings.kafka_consumer_group_id,
                "state": "Stable",
                "members": [],
                "lag": {}
            }
        ]

    async def get_consumer_lag(self, group_id: str) -> Dict[str, Any]:
        """Get consumer group lag information."""
        # This would require additional implementation
        # For now, return mock data
        return {
            "group_id": group_id,
            "total_lag": 0,
            "partitions": {}
        }

    async def unsubscribe_from_topic(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        try:
            # Cancel consumer task
            if topic in self._consumer_tasks:
                self._consumer_tasks[topic].cancel()
                del self._consumer_tasks[topic]

            # Stop consumer
            if topic in self.consumers:
                await self.consumers[topic].stop()
                del self.consumers[topic]

            # Remove handler
            if topic in self._message_handlers:
                del self._message_handlers[topic]

            logger.info("Unsubscribed from topic", topic=topic)

        except Exception as e:
            logger.error("Failed to unsubscribe from topic", error=str(e), topic=topic)

    async def is_healthy(self) -> bool:
        """Check if Kafka service is healthy."""
        try:
            if not self.is_running or not self.producer:
                return False

            # Try to get metadata (this will fail if Kafka is not reachable)
            await self.producer.client.check_version()
            return True

        except Exception as e:
            logger.debug("Kafka health check failed", error=str(e))
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "produced_count": self.produced_count,
            "consumed_count": self.consumed_count,
            "error_count": self.error_count,
            "is_running": self.is_running,
            "active_consumers": len(self.consumers),
            "consumer_topics": list(self.consumers.keys())
        }

    def _serialize_message(self, message: Dict[str, Any]) -> bytes:
        """Serialize message to JSON bytes."""
        return json.dumps(message, default=str).encode('utf-8')

    def _serialize_key(self, key: Optional[str]) -> Optional[bytes]:
        """Serialize message key."""
        return key.encode('utf-8') if key else None

    def _deserialize_message(self, message_bytes: bytes) -> Dict[str, Any]:
        """Deserialize message from JSON bytes."""
        return json.loads(message_bytes.decode('utf-8'))

    def _deserialize_key(self, key_bytes: Optional[bytes]) -> Optional[str]:
        """Deserialize message key."""
        return key_bytes.decode('utf-8') if key_bytes else None