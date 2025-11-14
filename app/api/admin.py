"""Administrative endpoints."""

from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.core.config import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()


class SystemStatus(BaseModel):
    """System status information."""
    status: str
    services: Dict[str, Any]
    configuration: Dict[str, Any]


class ServiceControl(BaseModel):
    """Service control request."""
    action: str  # start, stop, restart, pause, resume
    service: str  # kafka, kinesis, stream_processor


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    key: str
    value: Any
    restart_required: bool = False


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> SystemStatus:
    """Get comprehensive system status."""
    try:
        services = {}

        # Check Kafka service
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if kafka_service:
            services["kafka"] = {
                "status": "running" if await kafka_service.is_healthy() else "unhealthy",
                "bootstrap_servers": settings.kafka_bootstrap_servers,
                "consumer_groups": await kafka_service.list_consumer_groups() if hasattr(kafka_service, 'list_consumer_groups') else []
            }

        # Check Kinesis service
        kinesis_service = getattr(request.app.state, 'kinesis_service', None)
        if kinesis_service:
            services["kinesis"] = {
                "status": "running" if await kinesis_service.is_healthy() else "unhealthy",
                "region": settings.aws_default_region,
                "streams": await kinesis_service.list_streams() if hasattr(kinesis_service, 'list_streams') else []
            }

        # Check Stream Processor
        stream_processor = getattr(request.app.state, 'stream_processor', None)
        if stream_processor:
            services["stream_processor"] = {
                "status": "running" if stream_processor.is_running else "stopped",
                "processed_messages": getattr(stream_processor, 'processed_count', 0),
                "error_count": getattr(stream_processor, 'error_count', 0)
            }

        # Configuration summary
        configuration = {
            "debug_mode": settings.debug,
            "log_level": settings.log_level,
            "batch_size": settings.batch_size,
            "processing_timeout": settings.processing_timeout,
            "max_retries": settings.max_retries,
            "enable_stream_processing": settings.enable_stream_processing
        }

        overall_status = "healthy" if all(
            service.get("status") in ["running", "healthy"]
            for service in services.values()
        ) else "degraded"

        return SystemStatus(
            status=overall_status,
            services=services,
            configuration=configuration
        )

    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.post("/control")
async def control_service(
    control: ServiceControl,
    request: Request,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Control system services."""
    try:
        if control.service == "stream_processor":
            stream_processor = getattr(request.app.state, 'stream_processor', None)
            if not stream_processor:
                raise HTTPException(status_code=404, detail="Stream processor not found")

            if control.action == "start":
                if not stream_processor.is_running:
                    await stream_processor.start_processing()
                    logger.info("Stream processor started")
                    return {"status": "success", "message": "Stream processor started"}
                else:
                    return {"status": "info", "message": "Stream processor already running"}

            elif control.action == "stop":
                if stream_processor.is_running:
                    await stream_processor.stop()
                    logger.info("Stream processor stopped")
                    return {"status": "success", "message": "Stream processor stopped"}
                else:
                    return {"status": "info", "message": "Stream processor already stopped"}

            elif control.action == "restart":
                if stream_processor.is_running:
                    await stream_processor.stop()
                await stream_processor.start_processing()
                logger.info("Stream processor restarted")
                return {"status": "success", "message": "Stream processor restarted"}

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported action: {control.action}")

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported service: {control.service}")

    except Exception as e:
        logger.error("Failed to control service", error=str(e), service=control.service, action=control.action)
        raise HTTPException(status_code=500, detail=f"Failed to control service: {str(e)}")


@router.get("/logs")
async def get_recent_logs(
    lines: int = 100,
    level: str = "INFO",
    service: str = None
) -> List[Dict[str, Any]]:
    """Get recent application logs."""
    try:
        # This would typically read from a log aggregation system
        # For now, we'll return mock log entries

        mock_logs = [
            {
                "timestamp": "2023-12-01T10:30:00Z",
                "level": "INFO",
                "service": "kafka_service",
                "message": "Consumer group rebalanced",
                "context": {"group_id": "streaming-consumer-group", "partitions": 3}
            },
            {
                "timestamp": "2023-12-01T10:29:45Z",
                "level": "DEBUG",
                "service": "stream_processor",
                "message": "Processed batch of messages",
                "context": {"batch_size": 100, "processing_time_ms": 150}
            },
            {
                "timestamp": "2023-12-01T10:29:30Z",
                "level": "WARN",
                "service": "kinesis_service",
                "message": "Kinesis put record throttled",
                "context": {"stream": "user-analytics", "retry_count": 1}
            }
        ]

        # Filter by service if provided
        if service:
            mock_logs = [log for log in mock_logs if log["service"] == service]

        # Filter by level
        level_order = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
        min_level = level_order.get(level.upper(), 1)
        mock_logs = [
            log for log in mock_logs
            if level_order.get(log["level"], 1) >= min_level
        ]

        return mock_logs[:lines]

    except Exception as e:
        logger.error("Failed to get logs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.post("/config/update")
async def update_configuration(
    config: ConfigUpdate,
    request: Request,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Update runtime configuration."""
    try:
        # This would typically update configuration in a persistent store
        # For now, we'll simulate the update

        if config.key in ["log_level", "batch_size", "processing_timeout", "max_retries"]:
            logger.info(
                "Configuration updated",
                key=config.key,
                old_value=getattr(settings, config.key, None),
                new_value=config.value,
                restart_required=config.restart_required
            )

            response = {
                "status": "success",
                "message": f"Configuration '{config.key}' updated successfully",
                "restart_required": config.restart_required
            }

            if config.restart_required:
                response["warning"] = "Service restart required for changes to take effect"

            return response
        else:
            raise HTTPException(status_code=400, detail=f"Configuration key '{config.key}' is not updatable")

    except Exception as e:
        logger.error("Failed to update configuration", error=str(e), key=config.key)
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        import psutil
        import time

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        return {
            "timestamp": time.time(),
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }

    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.post("/maintenance/cleanup")
async def cleanup_resources(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Cleanup system resources."""
    try:
        cleanup_results = {}

        # Cleanup Kafka resources
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if kafka_service and hasattr(kafka_service, 'cleanup'):
            kafka_cleanup = await kafka_service.cleanup()
            cleanup_results["kafka"] = kafka_cleanup

        # Cleanup Kinesis resources
        kinesis_service = getattr(request.app.state, 'kinesis_service', None)
        if kinesis_service and hasattr(kinesis_service, 'cleanup'):
            kinesis_cleanup = await kinesis_service.cleanup()
            cleanup_results["kinesis"] = kinesis_cleanup

        # Cleanup stream processor
        stream_processor = getattr(request.app.state, 'stream_processor', None)
        if stream_processor and hasattr(stream_processor, 'cleanup'):
            processor_cleanup = await stream_processor.cleanup()
            cleanup_results["stream_processor"] = processor_cleanup

        logger.info("System cleanup completed", results=cleanup_results)

        return {
            "status": "success",
            "message": "System cleanup completed successfully",
            "details": cleanup_results
        }

    except Exception as e:
        logger.error("Failed to cleanup resources", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cleanup resources: {str(e)}")