"""Health check endpoints."""

from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.core.config import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    services: Dict[str, str]


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    status: str
    version: str
    services: Dict[str, Dict[str, Any]]
    system: Dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def health_check(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """Basic health check endpoint."""
    services = {}

    # Check Kafka service
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if kafka_service and hasattr(kafka_service, 'is_healthy'):
            services["kafka"] = "healthy" if await kafka_service.is_healthy() else "unhealthy"
        else:
            services["kafka"] = "unknown"
    except Exception as e:
        logger.warning("Kafka health check failed", error=str(e))
        services["kafka"] = "unhealthy"

    # Check Kinesis service
    try:
        kinesis_service = getattr(request.app.state, 'kinesis_service', None)
        if kinesis_service and hasattr(kinesis_service, 'is_healthy'):
            services["kinesis"] = "healthy" if await kinesis_service.is_healthy() else "unhealthy"
        else:
            services["kinesis"] = "unknown"
    except Exception as e:
        logger.warning("Kinesis health check failed", error=str(e))
        services["kinesis"] = "unhealthy"

    # Overall status
    overall_status = "healthy" if all(
        status == "healthy" for status in services.values()
    ) else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        services=services
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> DetailedHealthResponse:
    """Detailed health check with service metrics."""
    services = {}
    system_info = {}

    # Check Kafka service
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if kafka_service:
            kafka_info = {
                "status": "healthy" if await kafka_service.is_healthy() else "unhealthy",
                "bootstrap_servers": settings.kafka_bootstrap_servers,
                "consumer_group": settings.kafka_consumer_group_id,
            }
            if hasattr(kafka_service, 'get_metrics'):
                kafka_info["metrics"] = await kafka_service.get_metrics()
            services["kafka"] = kafka_info
        else:
            services["kafka"] = {"status": "unknown", "error": "Service not initialized"}
    except Exception as e:
        logger.error("Kafka detailed health check failed", error=str(e))
        services["kafka"] = {"status": "unhealthy", "error": str(e)}

    # Check Kinesis service
    try:
        kinesis_service = getattr(request.app.state, 'kinesis_service', None)
        if kinesis_service:
            kinesis_info = {
                "status": "healthy" if await kinesis_service.is_healthy() else "unhealthy",
                "region": settings.aws_default_region,
                "endpoint": settings.aws_endpoint_url,
            }
            if hasattr(kinesis_service, 'get_metrics'):
                kinesis_info["metrics"] = await kinesis_service.get_metrics()
            services["kinesis"] = kinesis_info
        else:
            services["kinesis"] = {"status": "unknown", "error": "Service not initialized"}
    except Exception as e:
        logger.error("Kinesis detailed health check failed", error=str(e))
        services["kinesis"] = {"status": "unhealthy", "error": str(e)}

    # Check Stream Processor
    try:
        stream_processor = getattr(request.app.state, 'stream_processor', None)
        if stream_processor:
            processor_info = {
                "status": "running" if stream_processor.is_running else "stopped",
                "processed_messages": getattr(stream_processor, 'processed_count', 0),
                "error_count": getattr(stream_processor, 'error_count', 0),
            }
            services["stream_processor"] = processor_info
        else:
            services["stream_processor"] = {"status": "unknown", "error": "Service not initialized"}
    except Exception as e:
        logger.error("Stream processor health check failed", error=str(e))
        services["stream_processor"] = {"status": "unhealthy", "error": str(e)}

    # System information
    import platform
    import psutil

    try:
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        }
    except Exception as e:
        logger.warning("Failed to get system info", error=str(e))
        system_info = {"error": "Unable to retrieve system information"}

    # Overall status
    service_statuses = []
    for service_data in services.values():
        if isinstance(service_data, dict):
            status = service_data.get("status", "unknown")
            service_statuses.append(status in ["healthy", "running"])
        else:
            service_statuses.append(service_data == "healthy")

    overall_status = "healthy" if all(service_statuses) else "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        version=settings.app_version,
        services=services,
        system=system_info
    )


@router.get("/ready")
async def readiness_check(request: Request) -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint."""
    try:
        # Check if all essential services are ready
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        kinesis_service = getattr(request.app.state, 'kinesis_service', None)

        if not kafka_service or not kinesis_service:
            raise HTTPException(status_code=503, detail="Services not initialized")

        # Check if services are healthy
        kafka_healthy = await kafka_service.is_healthy()
        kinesis_healthy = await kinesis_service.is_healthy()

        if not (kafka_healthy and kinesis_healthy):
            raise HTTPException(status_code=503, detail="Services not ready")

        return {"status": "ready"}

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}