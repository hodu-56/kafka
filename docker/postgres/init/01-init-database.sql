-- Initialize database for streaming project
-- This script sets up the database schema and sample data

-- Create streaming schema
CREATE SCHEMA IF NOT EXISTS streaming;

-- Grant privileges
GRANT ALL PRIVILEGES ON SCHEMA streaming TO postgres;

-- Create users table
CREATE TABLE IF NOT EXISTS streaming.users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    user_segment VARCHAR(50) DEFAULT 'bronze',
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00
);

-- Create orders table
CREATE TABLE IF NOT EXISTS streaming.orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shipping_address JSONB,
    items_count INTEGER DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0.00
);

-- Create order_items table
CREATE TABLE IF NOT EXISTS streaming.order_items (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    product_name VARCHAR(255),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_events table for tracking user activities
CREATE TABLE IF NOT EXISTS streaming.user_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Create product_views table for analytics
CREATE TABLE IF NOT EXISTS streaming.product_views (
    id SERIAL PRIMARY KEY,
    view_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    product_id VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    view_duration INTEGER, -- in seconds
    referrer_url TEXT,
    device_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_user_id ON streaming.users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON streaming.users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON streaming.users(created_at);

CREATE INDEX IF NOT EXISTS idx_orders_order_id ON streaming.orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON streaming.orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON streaming.orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON streaming.orders(created_at);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON streaming.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON streaming.order_items(product_id);

CREATE INDEX IF NOT EXISTS idx_user_events_user_id ON streaming.user_events(user_id);
CREATE INDEX IF NOT EXISTS idx_user_events_event_type ON streaming.user_events(event_type);
CREATE INDEX IF NOT EXISTS idx_user_events_created_at ON streaming.user_events(created_at);

CREATE INDEX IF NOT EXISTS idx_product_views_user_id ON streaming.product_views(user_id);
CREATE INDEX IF NOT EXISTS idx_product_views_product_id ON streaming.product_views(product_id);
CREATE INDEX IF NOT EXISTS idx_product_views_created_at ON streaming.product_views(created_at);

-- Create a trigger to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON streaming.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON streaming.orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO streaming.users (user_id, email, first_name, last_name, user_segment, total_orders, total_spent) VALUES
('user_001', 'john.doe@example.com', 'John', 'Doe', 'gold', 15, 1250.00),
('user_002', 'jane.smith@example.com', 'Jane', 'Smith', 'silver', 8, 650.00),
('user_003', 'bob.johnson@example.com', 'Bob', 'Johnson', 'bronze', 3, 180.00),
('user_004', 'alice.wilson@example.com', 'Alice', 'Wilson', 'platinum', 25, 3200.00),
('user_005', 'charlie.brown@example.com', 'Charlie', 'Brown', 'bronze', 1, 49.99)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO streaming.orders (order_id, user_id, status, total_amount, items_count, shipping_address) VALUES
('order_001', 'user_001', 'completed', 125.50, 3, '{"street": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"}'),
('order_002', 'user_002', 'processing', 89.99, 2, '{"street": "456 Oak Ave", "city": "Los Angeles", "state": "CA", "zip": "90001"}'),
('order_003', 'user_003', 'shipped', 45.00, 1, '{"street": "789 Pine Rd", "city": "Chicago", "state": "IL", "zip": "60601"}'),
('order_004', 'user_004', 'completed', 299.99, 5, '{"street": "321 Elm St", "city": "Houston", "state": "TX", "zip": "77001"}'),
('order_005', 'user_001', 'pending', 75.25, 2, '{"street": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"}')
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO streaming.order_items (order_id, product_id, product_name, quantity, unit_price, total_price) VALUES
('order_001', 'prod_001', 'Wireless Headphones', 1, 79.99, 79.99),
('order_001', 'prod_002', 'Phone Case', 2, 22.50, 45.00),
('order_002', 'prod_003', 'Bluetooth Speaker', 1, 89.99, 89.99),
('order_003', 'prod_004', 'USB Cable', 1, 15.00, 15.00),
('order_004', 'prod_005', 'Smart Watch', 1, 199.99, 199.99),
('order_004', 'prod_006', 'Watch Band', 2, 25.00, 50.00),
('order_005', 'prod_007', 'Wireless Charger', 1, 35.25, 35.25),
('order_005', 'prod_008', 'Screen Protector', 2, 20.00, 40.00);

INSERT INTO streaming.user_events (event_id, user_id, event_type, event_data, session_id, ip_address) VALUES
('evt_001', 'user_001', 'page_view', '{"page": "/home", "timestamp": "2024-01-15T10:00:00Z"}', 'sess_001', '192.168.1.1'),
('evt_002', 'user_001', 'product_view', '{"product_id": "prod_001", "category": "electronics"}', 'sess_001', '192.168.1.1'),
('evt_003', 'user_002', 'login', '{"method": "email", "success": true}', 'sess_002', '192.168.1.2'),
('evt_004', 'user_003', 'search', '{"query": "bluetooth speaker", "results_count": 25}', 'sess_003', '192.168.1.3'),
('evt_005', 'user_004', 'purchase', '{"order_id": "order_004", "amount": 299.99}', 'sess_004', '192.168.1.4');

INSERT INTO streaming.product_views (view_id, user_id, product_id, category, view_duration, device_type) VALUES
('view_001', 'user_001', 'prod_001', 'electronics', 45, 'desktop'),
('view_002', 'user_002', 'prod_003', 'electronics', 30, 'mobile'),
('view_003', 'user_003', 'prod_004', 'accessories', 15, 'tablet'),
('view_004', 'user_004', 'prod_005', 'wearables', 120, 'desktop'),
('view_005', 'user_001', 'prod_002', 'accessories', 25, 'desktop');

-- Create a publication for Debezium (if using pgoutput plugin)
-- This will be created by Debezium automatically, but we can pre-create it
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'dbz_publication') THEN
        CREATE PUBLICATION dbz_publication FOR TABLE
            streaming.users,
            streaming.orders,
            streaming.order_items,
            streaming.user_events,
            streaming.product_views;
    END IF;
END $$;

-- Grant replication privileges
ALTER USER postgres REPLICATION;

-- Enable logical replication for the slot
-- This will be handled by Debezium, but ensuring the configuration is correct
SELECT pg_create_logical_replication_slot('debezium_streaming', 'pgoutput')
WHERE NOT EXISTS (
    SELECT 1 FROM pg_replication_slots WHERE slot_name = 'debezium_streaming'
);

COMMIT;