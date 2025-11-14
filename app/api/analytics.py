"""Analytics and metrics endpoints."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()


class MetricPoint(BaseModel):
    """Single metric data point."""
    timestamp: datetime
    value: float
    labels: Optional[Dict[str, str]] = None


class MetricSeries(BaseModel):
    """Time series metric data."""
    name: str
    description: str
    unit: str
    data_points: List[MetricPoint]


class AnalyticsQuery(BaseModel):
    """Analytics query parameters."""
    metric_name: str
    start_time: datetime
    end_time: datetime
    aggregation: str = Field(default="avg", description="Aggregation method: avg, sum, count, max, min")
    group_by: Optional[List[str]] = Field(None, description="Fields to group by")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")


class AnalyticsResult(BaseModel):
    """Analytics query result."""
    query: AnalyticsQuery
    result: List[MetricSeries]
    total_points: int
    execution_time_ms: float


class StreamMetrics(BaseModel):
    """Stream processing metrics."""
    messages_processed: int
    messages_per_second: float
    error_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    active_consumers: int
    consumer_lag: Dict[str, int]


class UserAnalytics(BaseModel):
    """User behavior analytics."""
    total_users: int
    active_users_24h: int
    new_users_24h: int
    top_events: List[Dict[str, Any]]
    user_segments: Dict[str, int]


class OrderAnalytics(BaseModel):
    """Order and sales analytics."""
    total_orders: int
    orders_24h: int
    revenue_24h: float
    avg_order_value: float
    top_products: List[Dict[str, Any]]
    order_status_distribution: Dict[str, int]


@router.get("/metrics/stream", response_model=StreamMetrics)
async def get_stream_metrics(
    request: Request,
    time_range: int = Query(default=3600, description="Time range in seconds"),
    settings: Settings = Depends(get_settings)
) -> StreamMetrics:
    """Get real-time streaming metrics."""
    try:
        stream_processor = getattr(request.app.state, 'stream_processor', None)
        if not stream_processor:
            raise HTTPException(status_code=503, detail="Stream processor not available")

        # Get metrics from stream processor
        metrics = await stream_processor.get_metrics(time_range)

        return StreamMetrics(
            messages_processed=metrics.get("messages_processed", 0),
            messages_per_second=metrics.get("messages_per_second", 0.0),
            error_rate=metrics.get("error_rate", 0.0),
            latency_p50=metrics.get("latency_p50", 0.0),
            latency_p95=metrics.get("latency_p95", 0.0),
            latency_p99=metrics.get("latency_p99", 0.0),
            active_consumers=metrics.get("active_consumers", 0),
            consumer_lag=metrics.get("consumer_lag", {})
        )

    except Exception as e:
        logger.error("Failed to get stream metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stream metrics: {str(e)}")


@router.get("/metrics/users", response_model=UserAnalytics)
async def get_user_analytics(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> UserAnalytics:
    """Get user behavior analytics."""
    try:
        # This would typically query a data store or analytics service
        # For now, we'll return mock data

        return UserAnalytics(
            total_users=10000,
            active_users_24h=2500,
            new_users_24h=150,
            top_events=[
                {"event_type": "login", "count": 5000},
                {"event_type": "product_view", "count": 3200},
                {"event_type": "add_to_cart", "count": 1800},
                {"event_type": "purchase", "count": 450}
            ],
            user_segments={
                "new_users": 1500,
                "returning_users": 6000,
                "premium_users": 2500
            }
        )

    except Exception as e:
        logger.error("Failed to get user analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")


@router.get("/metrics/orders", response_model=OrderAnalytics)
async def get_order_analytics(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> OrderAnalytics:
    """Get order and sales analytics."""
    try:
        # This would typically query a data store or analytics service
        # For now, we'll return mock data

        return OrderAnalytics(
            total_orders=5000,
            orders_24h=150,
            revenue_24h=25000.50,
            avg_order_value=166.67,
            top_products=[
                {"product_id": 101, "name": "Laptop Stand", "orders": 45},
                {"product_id": 102, "name": "Wireless Mouse", "orders": 38},
                {"product_id": 103, "name": "Keyboard", "orders": 32}
            ],
            order_status_distribution={
                "pending": 50,
                "processing": 75,
                "completed": 120,
                "cancelled": 5
            }
        )

    except Exception as e:
        logger.error("Failed to get order analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get order analytics: {str(e)}")


@router.post("/query", response_model=AnalyticsResult)
async def execute_analytics_query(
    query: AnalyticsQuery,
    request: Request,
    settings: Settings = Depends(get_settings)
) -> AnalyticsResult:
    """Execute custom analytics query."""
    try:
        start_time = datetime.now()

        # This would typically execute against a real analytics engine
        # For now, we'll return mock data

        mock_data_points = []
        current_time = query.start_time

        while current_time <= query.end_time:
            mock_data_points.append(
                MetricPoint(
                    timestamp=current_time,
                    value=100.0 + (len(mock_data_points) % 10) * 5,
                    labels={"source": "mock"}
                )
            )
            current_time += timedelta(minutes=5)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        result = AnalyticsResult(
            query=query,
            result=[
                MetricSeries(
                    name=query.metric_name,
                    description=f"Mock data for {query.metric_name}",
                    unit="count",
                    data_points=mock_data_points
                )
            ],
            total_points=len(mock_data_points),
            execution_time_ms=execution_time
        )

        logger.info(
            "Analytics query executed",
            metric=query.metric_name,
            points=len(mock_data_points),
            execution_time_ms=execution_time
        )

        return result

    except Exception as e:
        logger.error("Failed to execute analytics query", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")


@router.get("/dashboards/realtime")
async def get_realtime_dashboard(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get real-time dashboard data."""
    try:
        # Aggregate multiple metrics for dashboard
        stream_processor = getattr(request.app.state, 'stream_processor', None)

        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "stream_metrics": {
                "messages_per_second": 150.5,
                "error_rate": 0.02,
                "consumer_lag": {"streaming-consumer-group": 100}
            },
            "user_activity": {
                "active_sessions": 1250,
                "new_registrations": 15,
                "page_views": 5000
            },
            "order_activity": {
                "orders_per_minute": 5.2,
                "revenue_per_minute": 850.75,
                "cart_abandonment_rate": 0.15
            },
            "system_health": {
                "kafka_status": "healthy",
                "kinesis_status": "healthy",
                "database_status": "healthy"
            }
        }

        if stream_processor:
            try:
                actual_metrics = await stream_processor.get_metrics(300)  # 5 minutes
                dashboard_data["stream_metrics"].update(actual_metrics)
            except Exception as e:
                logger.warning("Failed to get actual stream metrics", error=str(e))

        return dashboard_data

    except Exception as e:
        logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/alerts")
async def get_active_alerts(
    request: Request,
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
    settings: Settings = Depends(get_settings)
) -> List[Dict[str, Any]]:
    """Get active alerts and notifications."""
    try:
        # This would typically query an alerting system
        # For now, we'll return mock alerts

        mock_alerts = [
            {
                "id": "alert-001",
                "title": "High Consumer Lag",
                "description": "Consumer group 'streaming-consumer-group' has lag > 1000 messages",
                "severity": "medium",
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "status": "active",
                "metric": "consumer_lag",
                "value": 1250,
                "threshold": 1000
            },
            {
                "id": "alert-002",
                "title": "Error Rate Spike",
                "description": "Stream processing error rate increased to 5%",
                "severity": "high",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "status": "active",
                "metric": "error_rate",
                "value": 0.05,
                "threshold": 0.01
            }
        ]

        # Filter by severity if provided
        if severity:
            mock_alerts = [alert for alert in mock_alerts if alert["severity"] == severity]

        return mock_alerts

    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")