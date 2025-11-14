# 🌊 Kafka + Flink 실시간 스트림 처리 가이드

## 🏗️ **아키텍처 개요**

```
📊 데이터 흐름
FastAPI → Kafka Topics → Flink Stream Processing → 결과 저장/알림
  ↓           ↓              ↓                      ↓
Swagger UI  Kafka UI      Flink Web UI         실시간 분석 결과
```

## 🌐 **접속 가능한 서비스들**

| 서비스 | URL | 용도 |
|--------|-----|------|
| **🔥 FastAPI Swagger** | http://localhost:8888/docs | 이벤트 API 테스트 |
| **📊 Flink Web UI** | http://localhost:8085 | 스트림 처리 작업 모니터링 |
| **🔍 Kafka UI** | http://localhost:8082 | Kafka 토픽/메시지 확인 |
| **📈 Grafana** | http://localhost:3000 | 대시보드 (admin/admin) |
| **⚡ Prometheus** | http://localhost:9090 | 메트릭 수집 |

## 🔄 **실시간 스트림 처리 작업들**

### **1. 실시간 사용자 세션 분석**
- **입력**: `user_events` 토픽
- **처리**: 5분 슬라이딩 윈도우로 사용자별 세션 분석
- **출력**: `user_session_analytics` 토픽
- **기능**:
  - 세션 시작/종료 시간
  - 총 이벤트 수
  - 방문한 고유 페이지 수
  - 세션 지속 시간
  - 이벤트 타입 수집

### **2. 실시간 상품 인기도 분석**
- **입력**: `product_analytics` 토픽
- **처리**: 5분 텀블링 윈도우로 상품별 인기도 계산
- **출력**: `product_popularity_metrics` 토픽
- **기능**:
  - 조회수, 장바구니 추가, 구매 수 집계
  - 고유 사용자 수
  - 전환율 계산 (구매/조회)
  - 인기도 점수 (조회 1점, 장바구니 3점, 구매 10점)

### **3. 실시간 주문 이상 탐지**
- **입력**: `order_events` 토픽
- **처리**: 실시간 이상 패턴 탐지
- **출력**: `order_anomaly_alerts` 토픽
- **기능**:
  - 고액 주문 탐지 (100만원 이상)
  - 단기간 다중 주문 탐지 (10분 내 3건 이상)
  - 심각도 분류 (CRITICAL, HIGH, MEDIUM)

## 🧪 **실제 사용법**

### **Step 1: 이벤트 데이터 생성**
1. **Swagger UI 접속**: http://localhost:8888/docs
2. **사용자 이벤트 생성**:
```json
{
  "user_id": "user_123",
  "event_type": "login",
  "metadata": {
    "device": "mobile",
    "session_id": "sess_456"
  }
}
```

3. **상품 이벤트 생성**:
```json
{
  "product_id": "product_789",
  "action": "view",
  "user_id": "user_123",
  "session_id": "sess_456",
  "properties": {
    "category": "electronics",
    "price": 1200000
  }
}
```

4. **주문 이벤트 생성**:
```json
{
  "order_id": "order_999",
  "user_id": "user_123",
  "status": "paid",
  "total_amount": 1500000,
  "items": [{"product_id": "product_789", "quantity": 1}],
  "shipping_address": {"city": "Seoul"}
}
```

### **Step 2: Kafka에서 원본 데이터 확인**
1. **Kafka UI 접속**: http://localhost:8082
2. **Topics 탭**에서 다음 토픽들 확인:
   - `user_events`
   - `product_analytics`
   - `order_events`

### **Step 3: Flink 스트림 처리 작업 실행**

#### **A. Flink Web UI 접속**
```
http://localhost:8085
```

#### **B. SQL 작업 실행 (향후 SQL Gateway 사용)**
```sql
-- 실시간 사용자 세션 분석 실행
/flink-jobs/user-session-analytics.sql

-- 실시간 상품 인기도 분석 실행
/flink-jobs/product-popularity-analytics.sql

-- 실시간 주문 이상 탐지 실행
/flink-jobs/order-anomaly-detection.sql
```

### **Step 4: 처리된 결과 확인**
Kafka UI에서 다음 **결과 토픽들** 확인:
- `user_session_analytics` - 세션 분석 결과
- `product_popularity_metrics` - 상품 인기도 메트릭
- `order_anomaly_alerts` - 주문 이상 탐지 알림

## 🎯 **실제 비즈니스 시나리오**

### **1. E-commerce 실시간 추천 시스템**
```
사용자 행동 → Kafka → Flink 실시간 분석 → 개인화 추천 → 웹사이트 표시
```

### **2. 실시간 인벤토리 관리**
```
주문 이벤트 → Kafka → Flink 재고 계산 → 재고 부족 알림 → 자동 발주
```

### **3. 사기 탐지 시스템**
```
주문 패턴 → Kafka → Flink 이상 탐지 → 알림 → 관리자 검토
```

### **4. 실시간 대시보드**
```
모든 이벤트 → Kafka → Flink 집계 → Grafana → 실시간 차트
```

## 🔧 **고급 설정**

### **Flink 메모리 설정**
```yaml
# docker-compose.yml에서 조정 가능
FLINK_PROPERTIES: |
  jobmanager.memory.process.size: 2048m
  taskmanager.memory.process.size: 2048m
```

### **Kafka-Flink 커넥터 설정**
- **병렬 처리**: TaskManager 2개로 병렬 처리
- **체크포인트**: 장애 복구를 위한 상태 저장
- **워터마크**: 늦게 도착하는 데이터 처리 (5초 지연 허용)

### **윈도우 타입**
- **Tumbling Window**: 겹치지 않는 고정 크기 윈도우 (상품 인기도)
- **Sliding Window**: 겹치는 슬라이딩 윈도우 (사용자 세션)
- **Session Window**: 활동 기반 동적 윈도우

## 📊 **성능 메트릭**

### **Flink Web UI에서 확인 가능한 지표**
- **처리량**: 초당 레코드 수
- **지연 시간**: 이벤트 처리 시간
- **체크포인트**: 상태 저장 주기
- **백프레셔**: 처리 병목 상태

### **Kafka 메트릭**
- **토픽별 메시지 수**
- **프로듀서/컨슈머 처리량**
- **파티션별 지연**

## 🎯 **다음 단계**

1. **SQL Gateway 활성화**로 브라우저에서 SQL 직접 실행
2. **복잡한 이벤트 처리 (CEP)** 패턴 매칭
3. **기계학습 모델 통합** 실시간 예측
4. **다중 데이터 소스 조인** (DB, API, File)
5. **실시간 알림 시스템** (Slack, Email, SMS)

**🚀 이제 Kafka와 Flink로 진짜 실시간 스트림 처리를 경험해보세요!**