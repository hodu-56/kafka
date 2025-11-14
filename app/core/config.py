"""Application configuration settings."""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    app_name: str = Field(default="Kafka Streaming Project", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    # Database settings
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/sourcedb",
        env="DATABASE_URL"
    )
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="sourcedb", env="POSTGRES_DB")

    # Kafka settings
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_schema_registry_url: str = Field(
        default="http://localhost:8081", env="KAFKA_SCHEMA_REGISTRY_URL"
    )
    kafka_connect_url: str = Field(
        default="http://localhost:8083", env="KAFKA_CONNECT_URL"
    )
    kafka_consumer_group_id: str = Field(
        default="streaming-consumer-group", env="KAFKA_CONSUMER_GROUP_ID"
    )
    kafka_auto_offset_reset: str = Field(default="latest", env="KAFKA_AUTO_OFFSET_RESET")
    kafka_enable_auto_commit: bool = Field(default=True, env="KAFKA_ENABLE_AUTO_COMMIT")
    kafka_max_poll_records: int = Field(default=1000, env="KAFKA_MAX_POLL_RECORDS")

    # AWS/LocalStack settings
    aws_endpoint_url: Optional[str] = Field(
        default="http://localhost:4566", env="AWS_ENDPOINT_URL"
    )
    aws_access_key_id: str = Field(default="test", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="test", env="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")

    # Kinesis settings
    kinesis_processed_events_stream: str = Field(
        default="processed-events", env="KINESIS_PROCESSED_EVENTS_STREAM"
    )
    kinesis_user_analytics_stream: str = Field(
        default="user-analytics", env="KINESIS_USER_ANALYTICS_STREAM"
    )
    kinesis_order_analytics_stream: str = Field(
        default="order-analytics", env="KINESIS_ORDER_ANALYTICS_STREAM"
    )
    kinesis_alerts_stream: str = Field(
        default="real-time-alerts", env="KINESIS_ALERTS_STREAM"
    )
    kinesis_metrics_stream: str = Field(
        default="aggregated-metrics", env="KINESIS_METRICS_STREAM"
    )

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Stream Processing settings
    enable_stream_processing: bool = Field(default=True, env="ENABLE_STREAM_PROCESSING")
    batch_size: int = Field(default=1000, env="BATCH_SIZE")
    processing_timeout: int = Field(default=30, env="PROCESSING_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    backoff_multiplier: float = Field(default=2.0, env="BACKOFF_MULTIPLIER")

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Monitoring settings
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3000, env="GRAFANA_PORT")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def kafka_servers_list(self) -> List[str]:
        """Get Kafka servers as a list."""
        return [server.strip() for server in self.kafka_bootstrap_servers.split(",")]

    @property
    def is_local_development(self) -> bool:
        """Check if running in local development mode."""
        return self.debug or self.aws_endpoint_url is not None


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()