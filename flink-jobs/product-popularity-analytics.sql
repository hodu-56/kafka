-- 실시간 상품 인기도 분석
-- 상품 조회, 장바구니 추가, 구매 이벤트를 실시간으로 집계

-- 1. Source Table: Kafka의 product_analytics 토픽
CREATE TABLE product_analytics (
    event_id STRING,
    product_id STRING,
    action STRING,
    user_id STRING,
    session_id STRING,
    timestamp_field TIMESTAMP(3),
    properties MAP<STRING, STRING>,
    is_logged_in BOOLEAN,
    source STRING,
    version STRING,
    event_time AS TO_TIMESTAMP(timestamp_field),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'product_analytics',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-product-analytics',
    'format' = 'json',
    'scan.startup.mode' = 'latest-offset'
);

-- 2. Sink Table: 상품 인기도 집계 결과
CREATE TABLE product_popularity_metrics (
    product_id STRING,
    time_window STRING,
    total_views BIGINT,
    total_cart_adds BIGINT,
    total_purchases BIGINT,
    unique_users BIGINT,
    conversion_rate DOUBLE,
    popularity_score DOUBLE,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'product_popularity_metrics',
    'properties.bootstrap.servers' = 'kafka:29092',
    'format' = 'json'
);

-- 3. 실시간 상품 인기도 분석 쿼리
INSERT INTO product_popularity_metrics
SELECT
    product_id,
    '5min' as time_window,
    SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END) as total_views,
    SUM(CASE WHEN action = 'add_to_cart' THEN 1 ELSE 0 END) as total_cart_adds,
    SUM(CASE WHEN action = 'purchase' THEN 1 ELSE 0 END) as total_purchases,
    COUNT(DISTINCT user_id) as unique_users,
    CASE
        WHEN SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END) > 0
        THEN CAST(SUM(CASE WHEN action = 'purchase' THEN 1 ELSE 0 END) AS DOUBLE) /
             CAST(SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END) AS DOUBLE)
        ELSE 0.0
    END as conversion_rate,
    -- 인기도 점수 계산 (조회수 1점, 장바구니 3점, 구매 10점)
    (SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END) * 1.0 +
     SUM(CASE WHEN action = 'add_to_cart' THEN 1 ELSE 0 END) * 3.0 +
     SUM(CASE WHEN action = 'purchase' THEN 1 ELSE 0 END) * 10.0) as popularity_score,
    window_start,
    window_end
FROM TABLE(
    TUMBLE(TABLE product_analytics, DESCRIPTOR(event_time), INTERVAL '5' MINUTE)
)
WHERE product_id IS NOT NULL
GROUP BY product_id, window_start, window_end
HAVING COUNT(*) > 0;