"""Streaming data endpoints."""

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()


class StreamingMessage(BaseModel):
    """Streaming message model."""
    topic: str = Field(..., description="Kafka topic name")
    key: Optional[str] = Field(None, description="Message key")
    value: Dict[str, Any] = Field(..., description="Message payload")
    headers: Optional[Dict[str, str]] = Field(None, description="Message headers")


class StreamingResponse(BaseModel):
    """Streaming operation response."""
    success: bool
    message: str
    message_id: Optional[str] = None
    partition: Optional[int] = None
    offset: Optional[int] = None


class TopicInfo(BaseModel):
    """Kafka topic information."""
    name: str
    partitions: int
    replication_factor: int
    config: Dict[str, str]


class ConsumerGroupInfo(BaseModel):
    """Consumer group information."""
    group_id: str
    state: str
    members: List[Dict[str, Any]]
    lag: Dict[str, int]


@router.post("/produce", response_model=StreamingResponse)
async def produce_message(
    message: StreamingMessage,
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> StreamingResponse:
    """Produce a message to Kafka topic."""
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        # Send message to Kafka
        result = await kafka_service.produce_message(
            topic=message.topic,
            key=message.key,
            value=message.value,
            headers=message.headers or {}
        )

        logger.info(
            "Message produced successfully",
            topic=message.topic,
            partition=result.get("partition"),
            offset=result.get("offset")
        )

        # Optionally forward to Kinesis in background
        if settings.enable_stream_processing:
            background_tasks.add_task(
                forward_to_kinesis,
                request.app.state.kinesis_service,
                message.value,
                message.topic
            )

        return StreamingResponse(
            success=True,
            message="Message produced successfully",
            message_id=result.get("message_id"),
            partition=result.get("partition"),
            offset=result.get("offset")
        )

    except Exception as e:
        logger.error("Failed to produce message", error=str(e), topic=message.topic)
        raise HTTPException(status_code=500, detail=f"Failed to produce message: {str(e)}")


@router.get("/topics", response_model=List[TopicInfo])
async def list_topics(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> List[TopicInfo]:
    """List all Kafka topics."""
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        topics = await kafka_service.list_topics()
        return [
            TopicInfo(
                name=topic["name"],
                partitions=topic["partitions"],
                replication_factor=topic["replication_factor"],
                config=topic.get("config", {})
            )
            for topic in topics
        ]

    except Exception as e:
        logger.error("Failed to list topics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list topics: {str(e)}")


@router.get("/consumer-groups", response_model=List[ConsumerGroupInfo])
async def list_consumer_groups(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> List[ConsumerGroupInfo]:
    """List all consumer groups."""
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        groups = await kafka_service.list_consumer_groups()
        return [
            ConsumerGroupInfo(
                group_id=group["group_id"],
                state=group["state"],
                members=group.get("members", []),
                lag=group.get("lag", {})
            )
            for group in groups
        ]

    except Exception as e:
        logger.error("Failed to list consumer groups", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list consumer groups: {str(e)}")


@router.get("/consumer-groups/{group_id}/lag")
async def get_consumer_lag(
    group_id: str,
    request: Request,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get consumer group lag information."""
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        lag_info = await kafka_service.get_consumer_lag(group_id)
        return lag_info

    except Exception as e:
        logger.error("Failed to get consumer lag", error=str(e), group_id=group_id)
        raise HTTPException(status_code=500, detail=f"Failed to get consumer lag: {str(e)}")


@router.post("/topics/{topic_name}/create")
async def create_topic(
    topic_name: str,
    partitions: int = 3,
    replication_factor: int = 1,
    request: Request = None,
    settings: Settings = Depends(get_settings)
) -> StreamingResponse:
    """Create a new Kafka topic."""
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        await kafka_service.create_topic(
            topic_name=topic_name,
            partitions=partitions,
            replication_factor=replication_factor
        )

        logger.info(
            "Topic created successfully",
            topic=topic_name,
            partitions=partitions,
            replication_factor=replication_factor
        )

        return StreamingResponse(
            success=True,
            message=f"Topic '{topic_name}' created successfully"
        )

    except Exception as e:
        logger.error("Failed to create topic", error=str(e), topic=topic_name)
        raise HTTPException(status_code=500, detail=f"Failed to create topic: {str(e)}")


@router.delete("/topics/{topic_name}")
async def delete_topic(
    topic_name: str,
    request: Request,
    settings: Settings = Depends(get_settings)
) -> StreamingResponse:
    """Delete a Kafka topic."""
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        await kafka_service.delete_topic(topic_name)

        logger.info("Topic deleted successfully", topic=topic_name)

        return StreamingResponse(
            success=True,
            message=f"Topic '{topic_name}' deleted successfully"
        )

    except Exception as e:
        logger.error("Failed to delete topic", error=str(e), topic=topic_name)
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {str(e)}")


async def forward_to_kinesis(kinesis_service, data: Dict[str, Any], source_topic: str):
    """Background task to forward messages to Kinesis."""
    try:
        if kinesis_service:
            # Determine target stream based on source topic
            stream_mapping = {
                "streaming.users": "user-analytics",
                "streaming.orders": "order-analytics",
                "streaming.user_events": "processed-events",
                "streaming.product_views": "user-analytics",
            }

            target_stream = stream_mapping.get(source_topic, "processed-events")

            await kinesis_service.put_record(
                stream_name=target_stream,
                data=data,
                partition_key=str(data.get("id", "default"))
            )

            logger.info(
                "Message forwarded to Kinesis",
                source_topic=source_topic,
                target_stream=target_stream
            )

    except Exception as e:
        logger.error(
            "Failed to forward message to Kinesis",
            error=str(e),
            source_topic=source_topic
        )