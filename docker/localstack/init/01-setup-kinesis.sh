#!/bin/bash

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
sleep 10

# Create Kinesis streams
echo "Creating Kinesis streams..."

# Stream for processed events
awslocal kinesis create-stream \
    --stream-name processed-events \
    --shard-count 3

# Stream for user analytics
awslocal kinesis create-stream \
    --stream-name user-analytics \
    --shard-count 2

# Stream for order analytics
awslocal kinesis create-stream \
    --stream-name order-analytics \
    --shard-count 2

# Stream for real-time alerts
awslocal kinesis create-stream \
    --stream-name real-time-alerts \
    --shard-count 1

# Stream for aggregated metrics
awslocal kinesis create-stream \
    --stream-name aggregated-metrics \
    --shard-count 1

# Create S3 bucket for data archiving
echo "Creating S3 bucket..."
awslocal s3 mb s3://streaming-data-archive

# Create DynamoDB tables for state management
echo "Creating DynamoDB tables..."

# Table for stream processing checkpoints
awslocal dynamodb create-table \
    --table-name stream-checkpoints \
    --attribute-definitions \
        AttributeName=stream_name,AttributeType=S \
        AttributeName=partition_key,AttributeType=S \
    --key-schema \
        AttributeName=stream_name,KeyType=HASH \
        AttributeName=partition_key,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

# Table for user session state
awslocal dynamodb create-table \
    --table-name user-sessions \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Table for real-time aggregations
awslocal dynamodb create-table \
    --table-name real-time-aggregations \
    --attribute-definitions \
        AttributeName=metric_name,AttributeType=S \
        AttributeName=time_window,AttributeType=S \
    --key-schema \
        AttributeName=metric_name,KeyType=HASH \
        AttributeName=time_window,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

echo "LocalStack setup completed!"

# List created resources
echo "Created Kinesis streams:"
awslocal kinesis list-streams

echo "Created S3 buckets:"
awslocal s3 ls

echo "Created DynamoDB tables:"
awslocal dynamodb list-tables