#!/bin/bash

# Test streaming by generating sample data
echo "Testing streaming pipeline..."

# Insert test data into PostgreSQL to trigger CDC events
echo "Inserting test data..."

# Insert new users
docker-compose exec postgres psql -U postgres -d sourcedb -c "
INSERT INTO streaming.users (user_id, email, first_name, last_name, user_segment) VALUES
('test_user_' || extract(epoch from now())::text, 'test1@example.com', 'Test', 'User1', 'silver'),
('test_user_' || (extract(epoch from now()) + 1)::text, 'test2@example.com', 'Test', 'User2', 'gold');
"

# Insert new orders
docker-compose exec postgres psql -U postgres -d sourcedb -c "
INSERT INTO streaming.orders (order_id, user_id, status, total_amount, items_count) VALUES
('test_order_' || extract(epoch from now())::text, 'test_user_' || extract(epoch from now())::text, 'pending', 299.99, 3),
('test_order_' || (extract(epoch from now()) + 1)::text, 'test_user_' || (extract(epoch from now()) + 1)::text, 'processing', 199.99, 2);
"

# Insert user events
docker-compose exec postgres psql -U postgres -d sourcedb -c "
INSERT INTO streaming.user_events (event_id, user_id, event_type, event_data, ip_address) VALUES
('test_event_' || extract(epoch from now())::text, 'test_user_' || extract(epoch from now())::text, 'login', '{\"device\": \"mobile\", \"browser\": \"safari\"}'::jsonb, '192.168.1.100'),
('test_event_' || (extract(epoch from now()) + 1)::text, 'test_user_' || (extract(epoch from now()) + 1)::text, 'product_view', '{\"product_id\": 123, \"category\": \"electronics\"}'::jsonb, '192.168.1.101'),
('test_event_' || (extract(epoch from now()) + 2)::text, 'test_user_' || extract(epoch from now())::text, 'add_to_cart', '{\"product_id\": 456, \"quantity\": 2}'::jsonb, '192.168.1.100');
"

# Insert product views
docker-compose exec postgres psql -U postgres -d sourcedb -c "
INSERT INTO streaming.product_views (view_id, user_id, product_id, category, view_duration, device_type) VALUES
('view_' || extract(epoch from now())::text, 'test_user_' || extract(epoch from now())::text, 'prod_123', 'electronics', 45, 'desktop'),
('view_' || (extract(epoch from now()) + 1)::text, 'test_user_' || (extract(epoch from now()) + 1)::text, 'prod_456', 'clothing', 30, 'mobile'),
('view_' || (extract(epoch from now()) + 2)::text, 'test_user_' || extract(epoch from now())::text, 'prod_789', 'books', 120, 'tablet');
"

# Update existing records to trigger UPDATE events
docker-compose exec postgres psql -U postgres -d sourcedb -c "
UPDATE streaming.orders SET status = 'completed' WHERE order_id = 'order_001';
UPDATE streaming.users SET user_segment = 'platinum' WHERE user_id = 'user_001';
"

echo "Test data inserted. Checking Kafka topics for messages..."

# Wait a bit for CDC to process
sleep 10

# Check messages in Kafka topics
echo "Messages in streaming.users topic:"
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic streaming.users --from-beginning --max-messages 5 --timeout-ms 5000

echo -e "\nMessages in streaming.orders topic:"
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic streaming.orders --from-beginning --max-messages 5 --timeout-ms 5000

echo -e "\nMessages in streaming.user_events topic:"
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic streaming.user_events --from-beginning --max-messages 5 --timeout-ms 5000

echo -e "\nStreaming test completed! Check Kafka UI at http://localhost:8080 for more details."