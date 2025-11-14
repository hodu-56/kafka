#!/bin/bash

# Wait for Kafka Connect to be ready
echo "Waiting for Kafka Connect to be ready..."
while ! curl -s http://localhost:8083/connectors > /dev/null; do
    echo "Waiting for Kafka Connect..."
    sleep 5
done

echo "Kafka Connect is ready!"

# Create Debezium PostgreSQL connector
echo "Creating Debezium PostgreSQL connector..."
curl -X POST \
  http://localhost:8083/connectors \
  -H 'Content-Type: application/json' \
  -d @config/debezium/postgres-connector.json

# Check connector status
echo "Checking connector status..."
sleep 5
curl -s http://localhost:8083/connectors/postgres-streaming-connector/status | jq '.'

# List all connectors
echo "All connectors:"
curl -s http://localhost:8083/connectors | jq '.'

# Create sample topics if they don't exist
echo "Creating Kafka topics..."
docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic streaming.users --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic streaming.orders --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic streaming.order_items --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic streaming.user_events --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic streaming.product_views --partitions 3 --replication-factor 1 --if-not-exists

# List all topics
echo "All Kafka topics:"
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

echo "Debezium setup completed!"