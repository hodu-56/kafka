-- Initialize source database with sample tables for CDC
CREATE SCHEMA IF NOT EXISTS streaming;

-- Users table for user events
CREATE TABLE streaming.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Orders table for e-commerce events
CREATE TABLE streaming.orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES streaming.users(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE streaming.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES streaming.orders(id),
    product_id INTEGER NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events table for tracking user activities
CREATE TABLE streaming.user_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES streaming.users(id),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product views table for analytics
CREATE TABLE streaming.product_views (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES streaming.users(id),
    product_id INTEGER NOT NULL,
    product_category VARCHAR(50),
    session_id VARCHAR(100),
    view_duration INTEGER, -- in seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON streaming.users(email);
CREATE INDEX idx_orders_user_id ON streaming.orders(user_id);
CREATE INDEX idx_orders_status ON streaming.orders(status);
CREATE INDEX idx_order_items_order_id ON streaming.order_items(order_id);
CREATE INDEX idx_user_events_user_id ON streaming.user_events(user_id);
CREATE INDEX idx_user_events_type ON streaming.user_events(event_type);
CREATE INDEX idx_user_events_created_at ON streaming.user_events(created_at);
CREATE INDEX idx_product_views_user_id ON streaming.product_views(user_id);
CREATE INDEX idx_product_views_product_id ON streaming.product_views(product_id);
CREATE INDEX idx_product_views_created_at ON streaming.product_views(created_at);

-- Insert sample data
INSERT INTO streaming.users (username, email, first_name, last_name) VALUES
('john_doe', 'john@example.com', 'John', 'Doe'),
('jane_smith', 'jane@example.com', 'Jane', 'Smith'),
('bob_wilson', 'bob@example.com', 'Bob', 'Wilson'),
('alice_brown', 'alice@example.com', 'Alice', 'Brown'),
('charlie_davis', 'charlie@example.com', 'Charlie', 'Davis');

INSERT INTO streaming.orders (user_id, order_number, total_amount, status) VALUES
(1, 'ORD-001', 99.99, 'completed'),
(2, 'ORD-002', 149.50, 'processing'),
(3, 'ORD-003', 79.99, 'pending'),
(1, 'ORD-004', 199.99, 'completed'),
(4, 'ORD-005', 299.99, 'processing');

INSERT INTO streaming.order_items (order_id, product_id, product_name, quantity, unit_price) VALUES
(1, 101, 'Laptop Stand', 1, 99.99),
(2, 102, 'Wireless Mouse', 2, 29.99),
(2, 103, 'Keyboard', 1, 89.52),
(3, 104, 'Monitor', 1, 79.99),
(4, 105, 'Headphones', 1, 199.99),
(5, 106, 'Webcam', 1, 149.99),
(5, 107, 'USB Cable', 3, 49.99);

-- Enable logical replication for Debezium
ALTER TABLE streaming.users REPLICA IDENTITY FULL;
ALTER TABLE streaming.orders REPLICA IDENTITY FULL;
ALTER TABLE streaming.order_items REPLICA IDENTITY FULL;
ALTER TABLE streaming.user_events REPLICA IDENTITY FULL;
ALTER TABLE streaming.product_views REPLICA IDENTITY FULL;