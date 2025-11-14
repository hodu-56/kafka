# 🚀 Kafka 스트리밍 프로젝트 빠른 시작 가이드

이 가이드를 따라하면 **5분 안에** Kafka 스트리밍 시스템을 구동하고 실제 예제를 테스트할 수 있습니다.

## 📋 사전 요구사항

- Docker & Docker Compose
- curl (테스트용)
- jq (JSON 포맷팅용, 선택사항)

## 🏃‍♂️ 1단계: 서비스 시작

```bash
# 1. 프로젝트 디렉토리로 이동
cd kafka-streaming-project

# 2. 모든 서비스 시작 (자동 헬스체크 포함)
./scripts/start-services.sh
```

**실행 결과**: 약 2-3분 후 모든 서비스가 준비됩니다.

## 🧪 2단계: 예제 API 테스트

```bash
# 전체 시나리오 테스트 실행
./scripts/test-examples.sh
```

이 스크립트는 다음과 같은 실제 비즈니스 시나리오를 테스트합니다:
- 👤 사용자 로그인
- 📄 페이지 방문 추적
- 📱 상품 조회 및 장바구니 추가
- 💳 주문 생성 및 결제
- 🚚 배송 시작
- 📦 배치 데이터 처리

## 🌐 3단계: 웹 인터페이스 확인

| 서비스 | URL | 설명 |
|--------|-----|------|
| **FastAPI Swagger** | http://localhost:8888/docs | API 문서 및 테스트 |
| **Kafka UI** | http://localhost:8082 | Kafka 토픽 및 메시지 모니터링 |
| **Grafana** | http://localhost:3000 | 메트릭 대시보드 (admin/admin) |
| **Prometheus** | http://localhost:9090 | 메트릭 수집 시스템 |

## 📊 4단계: 실시간 데이터 확인

### Kafka UI에서 메시지 확인
1. http://localhost:8082 접속
2. **Topics** 탭 클릭
3. 다음 토픽들에서 메시지 확인:
   - `user_events` - 사용자 행동 데이터
   - `order_events` - 주문 상태 변경
   - `product_analytics` - 상품 분석 데이터
   - `user_sessions` - 세션 분석
   - `inventory_events` - 재고 변동
   - `notifications` - 알림 이벤트

### API 개별 테스트
```bash
# 사용자 이벤트 전송
curl -X POST http://localhost:8888/api/v1/examples/user-events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "event_type": "login",
    "metadata": {"device": "mobile", "location": "Seoul"}
  }'

# 상품 분석 이벤트 전송
curl -X POST http://localhost:8888/api/v1/examples/product-analytics \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_001",
    "action": "view",
    "session_id": "session_456",
    "properties": {"category": "electronics", "price": 100000}
  }'

# 스트리밍 상태 확인
curl http://localhost:8888/api/v1/examples/streaming-status
```

## 🔍 5단계: 실시간 로그 모니터링

```bash
# FastAPI 애플리케이션 로그
docker-compose logs -f streaming-app

# Kafka 로그
docker-compose logs -f kafka

# 모든 서비스 로그
docker-compose logs -f
```

## 📈 주요 API 엔드포인트

### 🎯 예제 API (새로 추가된 것들)
- `POST /api/v1/examples/user-events` - 사용자 행동 추적
- `POST /api/v1/examples/order-events` - 주문 상태 변경
- `POST /api/v1/examples/product-analytics` - 상품 분석
- `POST /api/v1/examples/batch-events` - 배치 처리
- `GET /api/v1/examples/streaming-status` - 스트리밍 상태

### ⚙️ 기존 API
- `POST /api/v1/streaming/produce` - 직접 Kafka 메시지 전송
- `GET /api/v1/streaming/topics` - Kafka 토픽 목록
- `GET /health` - 헬스 체크

## 🛑 서비스 중지

```bash
# 모든 서비스 중지
docker-compose down

# 데이터까지 완전 삭제
docker-compose down -v
```

## 🚨 문제 해결

### 포트 충돌 문제
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep -E '(8888|9092|5433|6380|8082|3000|9090)'

# 기존 프로세스 종료 후 재시작
docker-compose down && docker-compose up -d
```

### 서비스 준비 확인
```bash
# 개별 서비스 상태 확인
curl http://localhost:8888/health        # FastAPI
curl http://localhost:8082               # Kafka UI
curl http://localhost:4566/_localstack/health  # LocalStack
```

### 로그에서 오류 확인
```bash
# 특정 서비스의 오류 로그만 확인
docker-compose logs streaming-app | grep -i error
docker-compose logs kafka | grep -i error
```

## 🎯 사용법 요약

**1단계**: `./scripts/start-services.sh` (서비스 시작)
**2단계**: `./scripts/test-examples.sh` (예제 테스트)
**3단계**: http://localhost:8888/docs (API 문서)
**4단계**: http://localhost:8082 (Kafka UI)

이제 **실제 비즈니스 시나리오에서 Kafka가 어떻게 동작하는지** 경험해보세요! 🎉