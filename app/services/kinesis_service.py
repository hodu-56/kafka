"""Kinesis service for AWS streaming integration."""

import asyncio
import json
import boto3
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import hashlib
import uuid

import structlog
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class KinesisService:
    """AWS Kinesis service for streaming data integration."""

    def __init__(self):
        self.client = None
        self.is_running = False
        self._consumer_tasks: Dict[str, asyncio.Task] = {}
        self._stream_handlers: Dict[str, Callable] = {}

        # Metrics tracking
        self.produced_count = 0
        self.consumed_count = 0
        self.error_count = 0

    async def start(self) -> None:
        """Start Kinesis service."""
        try:
            logger.info("Starting Kinesis service")

            # Initialize Kinesis client
            self.client = boto3.client(
                'kinesis',
                endpoint_url=settings.aws_endpoint_url,
                region_name=settings.aws_default_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )

            self.is_running = True
            logger.info("Kinesis service started successfully")

        except Exception as e:
            logger.error("Failed to start Kinesis service", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop Kinesis service."""
        try:
            logger.info("Stopping Kinesis service")

            # Stop all consumer tasks
            for task in self._consumer_tasks.values():
                task.cancel()

            await asyncio.gather(*self._consumer_tasks.values(), return_exceptions=True)
            self._consumer_tasks.clear()

            self.is_running = False
            logger.info("Kinesis service stopped")

        except Exception as e:
            logger.error("Error stopping Kinesis service", error=str(e))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def put_record(
        self,
        stream_name: str,
        data: Dict[str, Any],
        partition_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Put a single record to Kinesis stream."""
        if not self.client or not self.is_running:
            raise RuntimeError("Kinesis service not started")

        try:
            # Add timestamp if not present
            if "timestamp" not in data:
                data["timestamp"] = datetime.now().isoformat()

            # Generate partition key if not provided
            if not partition_key:
                partition_key = str(uuid.uuid4())

            # Serialize data
            serialized_data = json.dumps(data, default=str)

            # Put record
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.put_record(
                    StreamName=stream_name,
                    Data=serialized_data,
                    PartitionKey=partition_key
                )
            )

            self.produced_count += 1

            result = {
                "stream_name": stream_name,
                "shard_id": response['ShardId'],
                "sequence_number": response['SequenceNumber'],
                "partition_key": partition_key
            }

            logger.debug(
                "Record put to Kinesis successfully",
                stream_name=stream_name,
                shard_id=response['ShardId'],
                sequence_number=response['SequenceNumber']
            )

            return result

        except (ClientError, BotoCoreError) as e:
            self.error_count += 1
            logger.error("Failed to put record to Kinesis", error=str(e), stream_name=stream_name)
            raise
        except Exception as e:
            self.error_count += 1
            logger.error("Unexpected error putting record to Kinesis", error=str(e), stream_name=stream_name)
            raise

    async def put_records(
        self,
        stream_name: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Put multiple records to Kinesis stream in batch."""
        if not self.client or not self.is_running:
            raise RuntimeError("Kinesis service not started")

        try:
            # Prepare records for batch put
            kinesis_records = []
            for record in records:
                data = record.get("data", {})

                # Add timestamp if not present
                if "timestamp" not in data:
                    data["timestamp"] = datetime.now().isoformat()

                partition_key = record.get("partition_key", str(uuid.uuid4()))

                kinesis_records.append({
                    'Data': json.dumps(data, default=str),
                    'PartitionKey': partition_key
                })

            # Put records in batches of 500 (Kinesis limit)
            batch_size = 500
            results = []
            failed_records = []

            for i in range(0, len(kinesis_records), batch_size):
                batch = kinesis_records[i:i + batch_size]

                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.put_records(
                        StreamName=stream_name,
                        Records=batch
                    )
                )

                # Process response
                for j, record_result in enumerate(response['Records']):
                    if 'ErrorCode' in record_result:
                        failed_records.append({
                            'index': i + j,
                            'error_code': record_result['ErrorCode'],
                            'error_message': record_result['ErrorMessage']
                        })
                    else:
                        results.append({
                            'shard_id': record_result['ShardId'],
                            'sequence_number': record_result['SequenceNumber']
                        })

            successful_count = len(results)
            failed_count = len(failed_records)
            self.produced_count += successful_count
            self.error_count += failed_count

            logger.info(
                "Batch put records completed",
                stream_name=stream_name,
                total_records=len(records),
                successful=successful_count,
                failed=failed_count
            )

            return {
                "stream_name": stream_name,
                "total_records": len(records),
                "successful_records": successful_count,
                "failed_records": failed_count,
                "successful_results": results,
                "failed_results": failed_records
            }

        except (ClientError, BotoCoreError) as e:
            self.error_count += len(records)
            logger.error("Failed to put records to Kinesis", error=str(e), stream_name=stream_name)
            raise
        except Exception as e:
            self.error_count += len(records)
            logger.error("Unexpected error putting records to Kinesis", error=str(e), stream_name=stream_name)
            raise

    async def create_stream(
        self,
        stream_name: str,
        shard_count: int = 1,
        stream_mode_details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new Kinesis stream."""
        if not self.client:
            raise RuntimeError("Kinesis service not started")

        try:
            # Check if stream already exists
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.describe_stream(StreamName=stream_name)
                )
                if response['StreamDescription']['StreamStatus'] == 'ACTIVE':
                    logger.info("Stream already exists and is active", stream_name=stream_name)
                    return {
                        "stream_name": stream_name,
                        "status": "exists",
                        "shard_count": len(response['StreamDescription']['Shards'])
                    }
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise

            # Create stream
            create_params = {
                'StreamName': stream_name
            }

            if stream_mode_details:
                create_params['StreamModeDetails'] = stream_mode_details
            else:
                create_params['ShardCount'] = shard_count

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.create_stream(**create_params)
            )

            # Wait for stream to become active
            waiter = self.client.get_waiter('stream_exists')
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: waiter.wait(
                    StreamName=stream_name,
                    WaiterConfig={'Delay': 5, 'MaxAttempts': 20}
                )
            )

            logger.info(
                "Stream created successfully",
                stream_name=stream_name,
                shard_count=shard_count
            )

            return {
                "stream_name": stream_name,
                "status": "created",
                "shard_count": shard_count
            }

        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to create Kinesis stream", error=str(e), stream_name=stream_name)
            raise
        except Exception as e:
            logger.error("Unexpected error creating Kinesis stream", error=str(e), stream_name=stream_name)
            raise

    async def delete_stream(self, stream_name: str) -> None:
        """Delete a Kinesis stream."""
        if not self.client:
            raise RuntimeError("Kinesis service not started")

        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.delete_stream(StreamName=stream_name)
            )

            logger.info("Stream deleted successfully", stream_name=stream_name)

        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to delete Kinesis stream", error=str(e), stream_name=stream_name)
            raise
        except Exception as e:
            logger.error("Unexpected error deleting Kinesis stream", error=str(e), stream_name=stream_name)
            raise

    async def list_streams(self) -> List[Dict[str, Any]]:
        """List all Kinesis streams."""
        if not self.client:
            raise RuntimeError("Kinesis service not started")

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.list_streams()
            )

            streams = []
            for stream_name in response['StreamNames']:
                try:
                    stream_desc = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.client.describe_stream(StreamName=stream_name)
                    )

                    streams.append({
                        "name": stream_name,
                        "status": stream_desc['StreamDescription']['StreamStatus'],
                        "shard_count": len(stream_desc['StreamDescription']['Shards']),
                        "retention_period": stream_desc['StreamDescription']['RetentionPeriodHours']
                    })
                except Exception as e:
                    logger.warning("Failed to describe stream", stream_name=stream_name, error=str(e))
                    streams.append({
                        "name": stream_name,
                        "status": "unknown",
                        "shard_count": 0,
                        "retention_period": 0
                    })

            return streams

        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to list Kinesis streams", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error listing Kinesis streams", error=str(e))
            raise

    async def is_healthy(self) -> bool:
        """Check if Kinesis service is healthy."""
        try:
            if not self.is_running or not self.client:
                return False

            # Try to list streams (this will fail if Kinesis is not reachable)
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.list_streams(Limit=1)
            )
            return True

        except Exception as e:
            logger.debug("Kinesis health check failed", error=str(e))
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "produced_count": self.produced_count,
            "consumed_count": self.consumed_count,
            "error_count": self.error_count,
            "is_running": self.is_running,
            "active_consumers": len(self._consumer_tasks)
        }

    def _generate_partition_key(self, data: Dict[str, Any]) -> str:
        """Generate a partition key based on data content."""
        # Use a hash of relevant fields to ensure even distribution
        key_data = str(data.get('user_id', '')) + str(data.get('timestamp', ''))
        return hashlib.md5(key_data.encode()).hexdigest()