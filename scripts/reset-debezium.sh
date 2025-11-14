#!/bin/bash

# Reset Debezium connector and clean up
echo "Resetting Debezium connector..."

# Delete existing connector
echo "Deleting existing connector..."
curl -X DELETE http://localhost:8083/connectors/postgres-streaming-connector

# Wait for deletion
sleep 5

# Delete topics (optional - be careful in production)
echo "Deleting Kafka topics..."
docker-compose exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic streaming.users
docker-compose exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic streaming.orders
docker-compose exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic streaming.order_items
docker-compose exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic streaming.user_events
docker-compose exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic streaming.product_views
docker-compose exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic streaming.schema-changes.inventory

# Clean up PostgreSQL replication slot
echo "Cleaning up PostgreSQL replication slot..."
docker-compose exec postgres psql -U postgres -d sourcedb -c "
SELECT pg_drop_replication_slot('debezium_streaming') WHERE EXISTS (
    SELECT 1 FROM pg_replication_slots WHERE slot_name = 'debezium_streaming'
);
"

# Drop publication
docker-compose exec postgres psql -U postgres -d sourcedb -c "
DROP PUBLICATION IF EXISTS dbz_publication;
"

echo "Debezium reset completed!"
echo "Run ./scripts/setup-debezium.sh to recreate the connector."