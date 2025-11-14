-- 실시간 주문 패턴 분석 및 이상 탐지
-- 주문 금액, 빈도, 패턴을 분석하여 이상한 주문을 탐지

-- 1. Source Table: Kafka의 order_events 토픽
CREATE TABLE order_events (
    event_id STRING,
    order_id STRING,
    user_id STRING,
    status STRING,
    timestamp_field TIMESTAMP(3),
    items ARRAY<MAP<STRING, STRING>>,
    total_amount DOUBLE,
    shipping_address MAP<STRING, STRING>,
    item_count BIGINT,
    source STRING,
    version STRING,
    event_time AS TO_TIMESTAMP(timestamp_field),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'order_events',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-order-analytics',
    'format' = 'json',
    'scan.startup.mode' = 'latest-offset'
);

-- 2. Sink Table: 주문 패턴 분석 결과
CREATE TABLE order_pattern_analysis (
    analysis_type STRING,
    user_id STRING,
    order_id STRING,
    metric_name STRING,
    metric_value DOUBLE,
    threshold_value DOUBLE,
    is_anomaly BOOLEAN,
    severity STRING,
    analysis_time TIMESTAMP(3),
    details MAP<STRING, STRING>
) WITH (
    'connector' = 'kafka',
    'topic' = 'order_anomaly_alerts',
    'properties.bootstrap.servers' = 'kafka:29092',
    'format' = 'json'
);

-- 3. 고액 주문 이상 탐지 (10분 윈도우)
INSERT INTO order_pattern_analysis
SELECT
    'high_value_order' as analysis_type,
    user_id,
    order_id,
    'total_amount' as metric_name,
    total_amount as metric_value,
    1000000.0 as threshold_value,  -- 100만원 이상
    CASE WHEN total_amount > 1000000.0 THEN TRUE ELSE FALSE END as is_anomaly,
    CASE
        WHEN total_amount > 5000000.0 THEN 'CRITICAL'
        WHEN total_amount > 2000000.0 THEN 'HIGH'
        ELSE 'MEDIUM'
    END as severity,
    event_time as analysis_time,
    MAP[
        'order_status', status,
        'item_count', CAST(item_count AS STRING),
        'city', shipping_address['city']
    ] as details
FROM order_events
WHERE status = 'paid' AND total_amount > 1000000.0;

-- 4. 단기간 다중 주문 탐지
CREATE VIEW user_order_frequency AS
SELECT
    user_id,
    COUNT(*) as order_count,
    SUM(total_amount) as total_spent,
    MIN(event_time) as first_order,
    MAX(event_time) as last_order,
    window_start,
    window_end
FROM TABLE(
    TUMBLE(TABLE order_events, DESCRIPTOR(event_time), INTERVAL '10' MINUTE)
)
WHERE status = 'paid'
GROUP BY user_id, window_start, window_end
HAVING COUNT(*) >= 3;  -- 10분 내 3건 이상 주문

INSERT INTO order_pattern_analysis
SELECT
    'frequent_orders' as analysis_type,
    user_id,
    CAST(NULL AS STRING) as order_id,
    'order_frequency' as metric_name,
    CAST(order_count AS DOUBLE) as metric_value,
    3.0 as threshold_value,
    TRUE as is_anomaly,
    CASE
        WHEN order_count >= 5 THEN 'HIGH'
        ELSE 'MEDIUM'
    END as severity,
    window_end as analysis_time,
    MAP[
        'total_spent', CAST(total_spent AS STRING),
        'time_span_minutes', CAST(EXTRACT(EPOCH FROM (last_order - first_order)) / 60 AS STRING)
    ] as details
FROM user_order_frequency;