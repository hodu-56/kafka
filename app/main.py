"""
FastAPI application for Kafka streaming project.
Handles large-scale streaming data processing with Kafka, Kinesis, and Debezium.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.api import health, streaming, analytics, admin, examples
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.services.kafka_service import KafkaService
from app.services.kinesis_service import KinesisService
from app.services.stream_processor import StreamProcessor

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Kafka Streaming Application", version=settings.app_version)

    # Initialize services
    kafka_service = KafkaService()
    kinesis_service = KinesisService()
    stream_processor = StreamProcessor(kafka_service, kinesis_service)

    # Store services in app state
    app.state.kafka_service = kafka_service
    app.state.kinesis_service = kinesis_service
    app.state.stream_processor = stream_processor

    # Start background tasks
    try:
        await kafka_service.start()
        await kinesis_service.start()

        # Start stream processing in background
        if settings.enable_stream_processing:
            asyncio.create_task(stream_processor.start_processing())

        logger.info("All services started successfully")

        yield

    except Exception as e:
        logger.error("Error during startup", error=str(e))
        raise
    finally:
        # Cleanup
        logger.info("Shutting down services")
        await kafka_service.stop()
        await kinesis_service.stop()
        await stream_processor.stop()
        logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Large-scale streaming data processing with Kafka, Kinesis, and Debezium",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(streaming.router, prefix="/api/v1/streaming", tags=["streaming"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(examples.router, prefix="/api/v1/examples", tags=["examples"])

    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler."""
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """Log all requests."""
        start_time = asyncio.get_event_loop().time()

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        # Process request
        response = await call_next(request)

        # Log response
        duration = asyncio.get_event_loop().time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
        )

        return response

    return app


# Create app instance
app = create_app()


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with basic application info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Large-scale streaming data processing with Kafka, Kinesis, and Debezium",
        "status": "running",
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/health",
    }