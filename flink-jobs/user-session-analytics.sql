-- 실시간 사용자 세션 분석
-- Kafka 토픽에서 사용자 이벤트를 읽어 세션별로 집계

-- 1. Source Table: Kafka의 user_events 토픽
CREATE TABLE user_events (
    event_id STRING,
    user_id STRING,
    event_type STRING,
    timestamp_field TIMESTAMP(3),
    page_url STRING,
    product_id STRING,
    amount DOUBLE,
    metadata MAP<STRING, STRING>,
    source STRING,
    version STRING,
    event_time AS TO_TIMESTAMP(timestamp_field),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'user_events',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-user-analytics',
    'format' = 'json',
    'scan.startup.mode' = 'latest-offset'
);

-- 2. Sink Table: 집계된 세션 데이터를 Kafka로 출력
CREATE TABLE user_session_summary (
    user_id STRING,
    session_start TIMESTAMP(3),
    session_end TIMESTAMP(3),
    total_events BIGINT,
    unique_pages BIGINT,
    total_time_spent BIGINT,
    event_types ARRAY<STRING>,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'user_session_analytics',
    'properties.bootstrap.servers' = 'kafka:29092',
    'format' = 'json'
);

-- 3. 실시간 세션 분석 쿼리
INSERT INTO user_session_summary
SELECT
    user_id,
    MIN(event_time) as session_start,
    MAX(event_time) as session_end,
    COUNT(*) as total_events,
    COUNT(DISTINCT page_url) as unique_pages,
    EXTRACT(EPOCH FROM (MAX(event_time) - MIN(event_time))) as total_time_spent,
    COLLECT(DISTINCT event_type) as event_types,
    window_start,
    window_end
FROM TABLE(
    HOP(TABLE user_events, DESCRIPTOR(event_time), INTERVAL '1' MINUTE, INTERVAL '5' MINUTE)
)
WHERE user_id IS NOT NULL
GROUP BY user_id, window_start, window_end;