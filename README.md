# Kafka + Flink Real-time Streaming Project

A comprehensive real-time streaming data processing system built with **Apache Kafka**, **Apache Flink**, **Kinesis**, **Debezium**, and **FastAPI**. This project demonstrates enterprise-grade streaming data processing with Change Data Capture (CDC), real-time stream analytics, event-driven architecture, and cross-platform streaming capabilities.

## 🏗️ Architecture

### **Real-time Stream Processing Pipeline**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │───▶│    Debezium     │───▶│      Kafka      │───▶│  Apache Flink   │
│   (Source DB)   │    │  (CDC Connector)│    │   (Message Bus) │    │ (Stream Engine) │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        ▲                       │
                                                        │                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│  Event Topics   │◀───│ Stream Analytics│───▶│   Result Data   │
│ (Event Producer)│    │ • user_events   │    │ • Windowing     │    │ • Aggregated    │
│ • Swagger UI    │    │ • order_events  │    │ • Joins         │    │ • Alerts        │
│ • REST APIs     │    │ • analytics     │    │ • Patterns      │    │ • Metrics       │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       ▲                       │
         ▼                       ▼                       │                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Kinesis      │    │    Kafka UI     │    │  Flink Web UI   │    │   Grafana       │
│  (AWS Streams)  │    │ (Topic Monitor) │    │ (Job Monitor)   │    │ (Dashboards)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │                       ▲
                                ▼                       ▼                       │
                    ┌─────────────────────────────────────────────────────────────┐
                    │                 Monitoring Stack                           │
                    │  Prometheus (Metrics) + Grafana (Visualization)           │
                    │  Redis (Caching) + LocalStack (AWS Services)              │
                    └─────────────────────────────────────────────────────────────┘
```

### **Stream Processing Flow**

```
📊 Event Generation → Kafka Topics → Flink Stream Jobs → Real-time Results
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  User Actions   │──▶│  user_events    │──▶│ Session Analytics│──▶│Session Summaries│
│  • Login        │   │  • Raw Events   │   │ • 5min Windows  │   │ • Duration      │
│  • Page Views   │   │  • JSON Format  │   │ • User Grouping │   │ • Page Count    │
│  • Purchases    │   │  • Partitioned  │   │ • Aggregations  │   │ • Event Types   │
└─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘

┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Product Events  │──▶│product_analytics│──▶│Popularity Engine│──▶│ Trending Items  │
│ • Views         │   │ • Interaction   │   │ • Conversion    │   │ • Scores        │
│ • Cart Adds     │   │ • User Context  │   │ • Popularity    │   │ • Rankings      │
│ • Purchases     │   │ • Properties    │   │ • Time Windows  │   │ • Metrics       │
└─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘

┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Order Events   │──▶│  order_events   │──▶│Anomaly Detection│──▶│  Alert System   │
│ • Creation      │   │ • Status Change │   │ • Pattern Match │   │ • High Value    │
│ • Payment       │   │ • Amount Info   │   │ • Threshold     │   │ • Fraud Alert   │
│ • Shipping      │   │ • User Data     │   │ • Frequency     │   │ • Notifications │
└─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘
```

## 🚀 Features

### **🌊 Real-time Stream Processing**
- **Apache Flink Integration**: Enterprise-grade stream processing engine
- **Windowing Operations**: Tumbling, sliding, and session windows
- **Complex Event Processing**: Pattern matching and anomaly detection
- **Stream Analytics**: Real-time aggregations, joins, and transformations

### **📡 Event-Driven Architecture**
- **Change Data Capture (CDC)**: Real-time database change streaming with Debezium
- **Multi-Platform Streaming**: Kafka and AWS Kinesis integration
- **Event Sourcing**: Complete audit trail of business events
- **Saga Pattern**: Distributed transaction management

### **🚀 High-Performance Processing**
- **Parallel Processing**: Multi-TaskManager Flink cluster setup
- **Async Streaming**: Non-blocking message processing with FastAPI
- **Configurable Parallelism**: Scalable processing pipeline
- **Checkpointing**: Fault-tolerant state management

### **📊 Business Intelligence**
- **Real-time Analytics**: Live user behavior and business metrics
- **Fraud Detection**: Real-time anomaly detection and alerting
- **Personalization**: Dynamic user profiling and recommendations
- **Operational Metrics**: End-to-end pipeline monitoring

### **🏗️ Enterprise Architecture**
- **Scalable Microservices**: Containerized services with Docker Compose
- **Service Discovery**: Container networking and health checks
- **Configuration Management**: Environment-based configuration
- **API Gateway**: FastAPI-based REST endpoints with Swagger UI

### **📈 Monitoring & Observability**
- **Prometheus Metrics**: Comprehensive system and business metrics
- **Grafana Dashboards**: Real-time visualization and alerting
- **Kafka UI**: Topic and message management interface
- **Flink Web UI**: Stream job monitoring and debugging

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- At least 8GB RAM (recommended for all services)

## 🛠️ Quick Start

### **⚡ 5-Minute Setup**

```bash
# 1. Clone and prepare
git clone <repository-url>
cd kafka-streaming-project

# 2. Start complete streaming infrastructure
./scripts/start-services.sh

# 3. Test real-time stream processing
./scripts/test-examples.sh
```

### **🔍 Step-by-Step Setup**

#### **1. Clone and Setup**
```bash
git clone <repository-url>
cd kafka-streaming-project

# Copy environment configuration
cp .env.example .env

# Make scripts executable
chmod +x scripts/*.sh
chmod +x docker/localstack/init/*.sh
```

#### **2. Start All Services**
```bash
# Start complete infrastructure (Kafka + Flink + FastAPI + Monitoring)
docker-compose up -d

# Or use the automated script with health checks
./scripts/start-services.sh
```

#### **3. Verify Services**
```bash
# Check all services are running
docker-compose ps

# Verify Kafka cluster
curl -s http://localhost:8082

# Verify Flink cluster
curl -s http://localhost:8085

# Verify FastAPI application
curl -s http://localhost:8888/health/
```

#### **4. Test Stream Processing Pipeline**
```bash
# Run comprehensive example tests
./scripts/test-examples.sh

# Or test individual components
curl -X POST http://localhost:8888/api/v1/examples/user-events \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "event_type": "login"}'
```

#### **5. Optional: Initialize CDC Pipeline**
```bash
# Setup Debezium PostgreSQL connector (for database change streams)
./scripts/setup-debezium.sh
```

## 📊 Accessing the Services

| Service | URL | Description | Use Case |
|---------|-----|-------------|----------|
| **🔥 FastAPI Swagger** | http://localhost:8888/docs | Interactive API docs & testing | **Generate events, test APIs** |
| **🌊 Flink Web UI** | http://localhost:8085 | Stream processing jobs monitor | **Monitor real-time processing** |
| **🔍 Kafka UI** | http://localhost:8082 | Kafka cluster & topics management | **View messages, manage topics** |
| **📊 Grafana** | http://localhost:3000 | Real-time dashboards (admin/admin) | **Business metrics visualization** |
| **⚡ Prometheus** | http://localhost:9090 | Metrics collection & alerting | **System performance monitoring** |
| **🔧 FastAPI App** | http://localhost:8888 | Main streaming application | **Health checks, admin APIs** |

### **🎯 Quick Access URLs**

#### **For Developers**
- **API Testing**: http://localhost:8888/docs
- **Stream Jobs**: http://localhost:8085
- **Message Inspection**: http://localhost:8082

#### **For Operations**
- **System Monitoring**: http://localhost:3000
- **Health Checks**: http://localhost:8888/health/
- **Metrics**: http://localhost:9090

#### **For Business Users**
- **Real-time Analytics**: http://localhost:3000
- **Event Streaming Status**: http://localhost:8888/api/v1/examples/streaming-status

## 🔧 Configuration

### **Environment Variables**

Key configuration options in `.env`:

```env
# Application
APP_NAME=Kafka Streaming Project
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/sourcedb

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_SCHEMA_REGISTRY_URL=http://schema-registry:8081
KAFKA_CONNECT_URL=http://kafka-connect:8083

# Stream Processing
ENABLE_STREAM_PROCESSING=true
BATCH_SIZE=1000
PROCESSING_TIMEOUT=30

# AWS/Kinesis (LocalStack)
AWS_ENDPOINT_URL=http://localstack:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# Redis Caching
REDIS_URL=redis://redis:6379/0
```

### **Flink Configuration**

Adjust memory and parallelism in `docker-compose.yml`:

```yaml
flink-jobmanager:
  environment:
    FLINK_PROPERTIES: |
      jobmanager.memory.process.size: 2048m
      taskmanager.memory.process.size: 2048m
      parallelism.default: 4

flink-taskmanager:
  scale: 3  # Number of TaskManagers
```

### **Scaling Configuration**

#### **FastAPI Application Scaling**
```yaml
streaming-app:
  deploy:
    replicas: 3  # Multiple API instances
    resources:
      limits:
        memory: 1G
        cpus: '0.5'
```

#### **Kafka Partitioning**
```bash
# Increase partitions for high-throughput topics
docker-compose exec kafka kafka-topics --alter \
  --bootstrap-server localhost:9092 \
  --topic user_events \
  --partitions 6
```

#### **Flink Parallelism**
```sql
-- Set parallelism for specific jobs
SET 'parallelism.default' = '4';
```

## 📈 Data Flow

### **1. Event Generation**
- **REST APIs**: FastAPI endpoints generate business events
- **Database CDC**: Debezium captures PostgreSQL table changes
- **External Systems**: Third-party event sources via Kafka Connect

### **2. Message Ingestion**
- **Kafka Topics**: Event storage and distribution
  - `user_events` - User behavior tracking
  - `product_analytics` - Product interaction data
  - `order_events` - Order lifecycle events
  - `streaming.users`, `streaming.orders` - CDC from database

### **3. Real-time Stream Processing (Apache Flink)**
- **Session Analytics**: 5-minute sliding windows for user session analysis
- **Product Popularity**: Real-time trending and conversion rate calculation
- **Anomaly Detection**: Pattern matching for fraud and unusual behavior
- **Stream Joins**: Enriching events with user profiles and product data

### **4. Stream Processing Outputs**
- **Analytics Topics**:
  - `user_session_analytics` - Aggregated session metrics
  - `product_popularity_metrics` - Real-time product rankings
  - `order_anomaly_alerts` - Fraud detection alerts
- **External Systems**:
  - **Kinesis**: AWS-compatible streaming for ML/analytics
  - **Databases**: Materialized views and aggregated tables
  - **Notification Systems**: Real-time alerts and recommendations

### **5. Monitoring & Visualization**
- **Prometheus**: Metrics collection from all components
- **Grafana**: Real-time dashboards and alerting
- **Kafka UI**: Topic and message inspection
- **Flink Web UI**: Stream job monitoring and debugging

## 🎯 API Endpoints

### **🔥 Business Event APIs**

#### **User Behavior Tracking**
```bash
# Track user events (login, page views, purchases)
POST /api/v1/examples/user-events
{
  "user_id": "user_123",
  "event_type": "login",
  "page_url": "https://shop.com/electronics",
  "metadata": {
    "device": "mobile",
    "location": "Seoul",
    "session_id": "sess_456"
  }
}
```

#### **Product Analytics**
```bash
# Track product interactions (views, cart adds, purchases)
POST /api/v1/examples/product-analytics
{
  "product_id": "smartphone_001",
  "action": "add_to_cart",
  "user_id": "user_123",
  "session_id": "sess_456",
  "properties": {
    "category": "electronics",
    "price": 1200000,
    "brand": "Samsung"
  }
}
```

#### **Order Processing**
```bash
# Track order lifecycle (created, paid, shipped, delivered)
POST /api/v1/examples/order-events
{
  "order_id": "order_789",
  "user_id": "user_123",
  "status": "paid",
  "total_amount": 2500000,
  "items": [
    {"product_id": "smartphone_001", "quantity": 1, "price": 1200000},
    {"product_id": "case_002", "quantity": 1, "price": 50000}
  ],
  "shipping_address": {"city": "Seoul", "district": "Gangnam"}
}
```

#### **Batch Processing**
```bash
# Process multiple events in batch
POST /api/v1/examples/batch-events?topic=user_batch_events
[
  {"user_id": "user_001", "action": "login", "timestamp": "2024-01-01T10:00:00"},
  {"user_id": "user_002", "action": "purchase", "product_id": "prod_001"},
  {"user_id": "user_003", "action": "logout", "session_duration": 1800}
]
```

### **⚙️ System APIs**

#### **Stream Status Monitoring**
```bash
# Get real-time streaming status
GET /api/v1/examples/streaming-status
# Returns: Kafka health, metrics, active topics

# Check application health
GET /health/
# Returns: Service status, Kafka connectivity, processing metrics
```

#### **Low-level Kafka Operations**
```bash
# Direct Kafka message production
POST /api/v1/streaming/produce
{
  "topic": "custom_events",
  "key": "partition_key",
  "value": {"custom": "data"},
  "headers": {"source": "api"}
}

# List Kafka topics
GET /api/v1/streaming/topics

# Get consumer group information
GET /api/v1/streaming/consumer-groups
```

#### **Administration**
```bash
# Create new Kafka topic
POST /api/v1/streaming/topics/my_topic/create?partitions=3&replication_factor=1

# List Kinesis streams
GET /api/v1/admin/kinesis/streams

# Cross-platform streaming
POST /api/v1/streaming/kafka-to-kinesis
```

### **📊 Analytics APIs**
```bash
# Processing performance metrics
GET /api/v1/analytics/processing-metrics

# Real-time business aggregations
GET /api/v1/analytics/realtime-aggregations

# Stream processing statistics
GET /api/v1/analytics/stream-stats
```

## 🧪 Testing

### **🔄 Stream Processing Pipeline Testing**

#### **Complete End-to-End Test**
```bash
# Test entire Kafka + Flink pipeline
./scripts/test-examples.sh

# Or test individual components step by step
./scripts/test-streaming.sh
```

#### **Kafka Event Testing**
```bash
# Test individual event APIs via curl
curl -X POST http://localhost:8888/api/v1/examples/user-events \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "event_type": "login"}'

# Test batch event processing
curl -X POST http://localhost:8888/api/v1/examples/batch-events?topic=test_batch \
  -H "Content-Type: application/json" \
  -d '[{"user_id": "u1", "action": "purchase"}]'
```

#### **Flink Stream Processing Testing**
```bash
# Verify Flink cluster health
curl -s http://localhost:8085/overview

# Check running Flink jobs
curl -s http://localhost:8085/jobs

# Monitor job metrics
curl -s http://localhost:8085/jobs/overview
```

#### **Message Flow Verification**
```bash
# Verify Kafka topics have messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic user_events \
  --from-beginning --max-messages 5

# Verify Flink processing results
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic user_session_analytics \
  --from-beginning --max-messages 5
```

### **⚡ Performance Testing**

#### **Load Testing**
```bash
# Generate high-volume test data
./scripts/load-test.sh

# Monitor system performance
docker stats

# Monitor Kafka performance
curl -s http://localhost:8082/api/clusters/local/topics
```

#### **Flink Performance Testing**
```bash
# Monitor Flink TaskManager performance
curl -s http://localhost:8085/taskmanagers

# Check processing throughput
curl -s http://localhost:8085/jobs/{job-id}/metrics
```

### **🧪 Unit Tests**
```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI application tests
pytest tests/ -v

# Run Kafka service tests
pytest tests/test_kafka_service.py -v

# Run streaming pipeline tests
pytest tests/test_streaming.py -v
```

### **🔍 Integration Testing**
```bash
# Test complete data flow
python tests/integration/test_kafka_flink_pipeline.py

# Test cross-platform streaming (Kafka → Kinesis)
python tests/integration/test_cross_platform.py
```

## 📊 Monitoring

### **🔍 Real-time Monitoring Stack**

#### **Comprehensive Metrics Collection**
- **Kafka Metrics**: Message throughput, consumer lag, partition distribution, producer/consumer performance
- **Flink Metrics**: Job performance, checkpoint duration, processing latency, backpressure, TaskManager resources
- **Streaming Pipeline**: End-to-end processing rate, error rate, message flow latency
- **System Resources**: CPU, memory, disk usage, network I/O across all containers
- **Business Metrics**: User events, order processing, analytics results, real-time KPIs

#### **📈 Monitoring Interfaces**

| **Component** | **URL** | **Purpose** | **Key Metrics** |
|---------------|---------|-------------|-----------------|
| **🌊 Flink Web UI** | http://localhost:8085 | Stream processing jobs monitoring | Job status, throughput, latency, checkpoints |
| **📊 Grafana Dashboards** | http://localhost:3000 | Unified visualization (admin/admin) | All metrics with real-time charts |
| **🔍 Kafka UI** | http://localhost:8082 | Kafka cluster management | Topics, partitions, consumer groups, messages |
| **⚡ Prometheus** | http://localhost:9090 | Metrics collection & alerting | Raw metrics, custom queries, alerts |

### **🎯 Key Monitoring Dashboards**

#### **1. Kafka + Flink Overview Dashboard**
- **Kafka Cluster Health**: Broker status, topic distribution, consumer lag
- **Flink Cluster Status**: JobManager/TaskManager health, available slots
- **Message Flow**: End-to-end throughput from API → Kafka → Flink → Results
- **Processing Latency**: Real-time latency measurements across the pipeline

#### **2. Stream Processing Performance**
- **Flink Job Metrics**:
  - Records processed per second
  - Processing latency (P50, P95, P99)
  - Checkpoint success rate and duration
  - Backpressure indicators
- **Resource Utilization**: CPU, memory usage per TaskManager
- **Error Rates**: Failed records, exception counts

#### **3. Business Intelligence Dashboard**
- **Real-time User Activity**: Login events, page views, session analytics
- **Product Performance**: View counts, conversion rates, popularity scores
- **Order Analytics**: Order volume, anomaly alerts, revenue metrics
- **Cross-platform Streaming**: Kafka → Kinesis data flow metrics

#### **4. System Infrastructure Monitoring**
- **Container Resources**: Docker container CPU, memory, disk usage
- **Network Performance**: Inter-service communication latency
- **Database Performance**: PostgreSQL connection pools, query performance
- **Cache Performance**: Redis hit/miss rates, memory usage

### **🚨 Alerting & Notifications**

#### **Critical Alerts**
```yaml
# Example Prometheus alerting rules
- Kafka consumer lag > 1000 messages
- Flink job failure or restart
- Processing latency > 30 seconds
- System memory usage > 85%
- Order anomaly detection (CRITICAL severity)
```

#### **Alert Channels**
- **Grafana Notifications**: Built-in alerting system
- **Prometheus AlertManager**: Advanced alerting rules
- **FastAPI Health Endpoints**: Programmatic health checks
- **Custom Webhooks**: Integration with external monitoring systems

### **📏 Performance Benchmarks**

#### **Expected Performance Metrics**
- **Kafka Throughput**: 10,000+ messages/second per partition
- **Flink Processing**: Sub-second latency for simple aggregations
- **End-to-End Latency**: < 5 seconds from API call to processed result
- **System Resources**: < 70% CPU, < 80% memory under normal load

#### **Scaling Indicators**
- **Scale Up Kafka**: When consumer lag consistently > 5000
- **Scale Up Flink**: When backpressure indicators show consistent pressure
- **Scale Up System**: When resource utilization > 80% for extended periods

## 🔧 Maintenance

### Reset Pipeline
```bash
# Reset Debezium and clean topics
./scripts/reset-debezium.sh

# Restart services
docker-compose restart

# Recreate connector
./scripts/setup-debezium.sh
```

### Scaling Up
```bash
# Add Kafka partitions
docker-compose exec kafka kafka-topics --alter \
  --bootstrap-server localhost:9092 \
  --topic streaming.orders \
  --partitions 6

# Scale processing workers
docker-compose up -d --scale streaming-app=3
```

### Backup and Recovery
```bash
# Backup PostgreSQL data
docker-compose exec postgres pg_dump -U postgres sourcedb > backup.sql

# Export Kafka topics
# (Use Kafka Connect HDFS/S3 connectors for production)
```

## 🚨 Troubleshooting

### **🔍 Common Issues & Solutions**

#### **1. Service Startup Issues**

**Problem**: Services not starting or failing health checks
```bash
# Diagnose service issues
docker-compose ps
docker-compose logs [service-name]

# Check service dependencies
docker-compose logs --tail=50 kafka
docker-compose logs --tail=50 flink-jobmanager

# Restart specific services
docker-compose restart [service-name]

# Complete restart with cleanup
docker-compose down -v
docker-compose up -d
```

#### **2. Kafka Connection Issues**

**Problem**: FastAPI cannot connect to Kafka or Kafka UI shows errors
```bash
# Verify Kafka is accessible
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check internal network connectivity
docker-compose exec streaming-app curl -f kafka:29092

# Verify environment variables
docker-compose exec streaming-app env | grep KAFKA

# Fix: Ensure KAFKA_BOOTSTRAP_SERVERS uses internal Docker network
# .env should have: KAFKA_BOOTSTRAP_SERVERS=kafka:29092
```

#### **3. Flink Cluster Issues**

**Problem**: Flink jobs not starting or TaskManagers disconnecting
```bash
# Check Flink cluster status
curl -s http://localhost:8085/overview
curl -s http://localhost:8085/taskmanagers

# Verify Flink logs
docker-compose logs flink-jobmanager
docker-compose logs flink-taskmanager

# Common fixes:
# 1. Increase memory limits in docker-compose.yml
# 2. Check port conflicts (Flink Web UI on 8085)
# 3. Verify Flink job files are mounted correctly
docker-compose exec flink-jobmanager ls -la /opt/flink/usrlib/
```

**Flink Job Deployment Issues**:
```bash
# Submit Flink SQL job manually
docker-compose exec flink-jobmanager /opt/flink/bin/sql-client.sh

# Or via REST API
curl -X POST http://localhost:8085/jars/upload \
  -H "Content-Type: multipart/form-data" \
  -F "jarfile=@/path/to/job.jar"
```

#### **4. Debezium CDC Issues**

**Problem**: Database changes not streaming to Kafka
```bash
# Check PostgreSQL replication settings
docker-compose exec postgres psql -U postgres -c "SHOW wal_level;"
docker-compose exec postgres psql -U postgres -c "SHOW max_replication_slots;"

# Verify Debezium connector status
curl -s http://localhost:8083/connectors/postgres-source/status

# Reset and recreate connector
./scripts/reset-debezium.sh
./scripts/setup-debezium.sh

# Check CDC topics are created
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list | grep streaming
```

#### **5. Memory and Performance Issues**

**Problem**: High memory usage or slow processing
```bash
# Monitor resource usage
docker stats

# Check Java heap usage
docker-compose logs kafka | grep -i "outofmemoryerror"
docker-compose logs flink-jobmanager | grep -i "memory"

# Tuning options:
```

**Memory Configuration** (docker-compose.yml):
```yaml
# Kafka memory tuning
kafka:
  environment:
    KAFKA_HEAP_OPTS: "-Xmx2G -Xms2G"

# Flink memory tuning
flink-jobmanager:
  environment:
    FLINK_PROPERTIES: |
      jobmanager.memory.process.size: 2048m
      taskmanager.memory.process.size: 2048m
      taskmanager.memory.managed.fraction: 0.4
```

#### **6. Cross-Platform Streaming Issues**

**Problem**: Kafka to Kinesis streaming not working
```bash
# Check LocalStack (AWS services) status
curl -s http://localhost:4566/health

# Verify Kinesis streams exist
docker-compose exec streaming-app aws --endpoint-url=http://localstack:4566 \
  kinesis list-streams --region us-east-1

# Check AWS credentials in environment
docker-compose exec streaming-app env | grep AWS
```

### **🛠️ Performance Tuning**

#### **1. Kafka Optimization**
```yaml
# Producer optimization
KAFKA_PROPERTIES: |
  batch.size=65536
  linger.ms=5
  compression.type=snappy
  acks=1

# Consumer optimization
CONSUMER_PROPERTIES: |
  fetch.min.bytes=50000
  fetch.max.wait.ms=500
```

#### **2. Flink Optimization**
```yaml
FLINK_PROPERTIES: |
  # Checkpoint configuration
  execution.checkpointing.interval: 60000
  execution.checkpointing.min-pause: 5000

  # Parallelism tuning
  parallelism.default: 4
  taskmanager.numberOfTaskSlots: 2

  # Memory tuning
  taskmanager.memory.process.size: 2048m
  taskmanager.memory.managed.fraction: 0.4
```

#### **3. Database Optimization**
```sql
-- PostgreSQL optimization for CDC
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
SELECT pg_reload_conf();
```

### **🔄 Recovery Procedures**

#### **Complete System Reset**
```bash
# Nuclear option: reset everything
docker-compose down -v
docker system prune -f
docker volume prune -f

# Restart with fresh state
docker-compose up -d
./scripts/start-services.sh
```

#### **Selective Service Recovery**
```bash
# Restart just streaming components
docker-compose restart kafka flink-jobmanager flink-taskmanager streaming-app

# Reset Kafka topics (data loss!)
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --delete --topic user_events,product_analytics,order_events
```


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 📚 Additional Resources

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Debezium Documentation](https://debezium.io/documentation/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Kinesis Documentation](https://docs.aws.amazon.com/kinesis/)

---

## 🏷️ Project Structure

```
kafka-streaming-project/
├── app/                          # 🚀 FastAPI Application
│   ├── api/                     # API route handlers
│   │   ├── examples.py          # Business event streaming APIs
│   │   ├── streaming.py         # Low-level Kafka operations
│   │   ├── analytics.py         # Real-time analytics endpoints
│   │   └── admin.py            # Administrative APIs
│   ├── core/                   # Core application configuration
│   │   ├── config.py           # Settings and environment variables
│   │   └── dependencies.py     # Dependency injection
│   ├── models/                 # Database models
│   ├── schemas/                # Pydantic data validation schemas
│   │   ├── events.py           # Event schema definitions
│   │   └── analytics.py        # Analytics response schemas
│   └── services/               # Business logic services
│       ├── kafka_service.py    # Kafka producer/consumer service
│       ├── kinesis_service.py  # AWS Kinesis integration
│       └── analytics_service.py # Real-time analytics processing
├── flink-jobs/                  # 🌊 Apache Flink Stream Processing Jobs
│   ├── user-session-analytics.sql     # Real-time user session analysis
│   ├── product-popularity-analytics.sql # Product popularity calculation
│   └── order-anomaly-detection.sql    # Fraud detection & anomaly alerts
├── config/                     # 🔧 Configuration Files
│   ├── debezium/              # Debezium CDC connectors
│   │   └── postgres-connector.json # PostgreSQL CDC configuration
│   ├── grafana/               # Grafana dashboards & provisioning
│   │   ├── dashboards/        # Pre-built dashboard definitions
│   │   └── provisioning/      # Auto-provisioning configuration
│   └── prometheus/            # Prometheus monitoring configuration
│       └── prometheus.yml     # Metrics collection rules
├── docker/                     # 🐳 Docker Initialization Scripts
│   ├── postgres/              # PostgreSQL initialization
│   │   └── init/             # Database schema setup scripts
│   └── localstack/           # LocalStack (AWS services) setup
│       └── init/             # Kinesis stream initialization
├── scripts/                    # 🛠️ Utility & Automation Scripts
│   ├── start-services.sh      # Complete infrastructure startup
│   ├── test-examples.sh       # End-to-end pipeline testing
│   ├── setup-debezium.sh      # CDC connector setup
│   ├── reset-debezium.sh      # CDC pipeline reset
│   └── load-test.sh          # Performance load testing
├── tests/                      # 🧪 Test Suite
│   ├── unit/                  # Unit tests for services
│   ├── integration/           # Integration tests for pipelines
│   └── performance/           # Load and performance tests
├── logs/                       # 📝 Application Logs
│   ├── fastapi/              # FastAPI application logs
│   └── flink/                # Flink job execution logs
├── docker-compose.yml          # 🐳 Service Orchestration (Kafka, Flink, FastAPI, etc.)
├── Dockerfile                  # FastAPI application container definition
├── requirements.txt           # Python dependencies
├── .env.example              # Environment configuration template
├── README.md                 # 📚 Project documentation (this file)
├── KAFKA_FLINK_GUIDE.md      # 🌊 Kafka + Flink usage guide
└── .gitignore               # Git ignore patterns
```

### **🎯 Key Architecture Components**

#### **FastAPI Application (`app/`)**
- **Event APIs**: RESTful endpoints for business event ingestion
- **Streaming Services**: Kafka and Kinesis integration services
- **Real-time Analytics**: Live data processing and aggregation APIs

#### **Flink Stream Processing Jobs (`flink-jobs/`)**
- **SQL-based Processing**: Declarative stream processing with Flink SQL
- **Real-time Analytics**: Windowed aggregations and pattern matching
- **Event Processing**: Complex event processing (CEP) for anomaly detection

#### **Configuration Management (`config/`)**
- **Service Configuration**: Environment-specific settings for all services
- **Monitoring Setup**: Pre-configured dashboards and alerting rules
- **CDC Configuration**: Change Data Capture connector definitions

#### **Automation Scripts (`scripts/`)**
- **Infrastructure Management**: Automated startup, testing, and maintenance
- **Development Tools**: Load testing, debugging, and pipeline management
- **Deployment Automation**: Service health checks and recovery procedures