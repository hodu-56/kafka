#!/bin/bash

# Kafka 스트리밍 예제 API 테스트 스크립트
set -e

BASE_URL="http://localhost:8888"
EXAMPLES_API="$BASE_URL/api/v1/examples"

echo "🔧 Kafka 스트리밍 예제 API 테스트를 시작합니다..."

# 서비스 상태 확인
echo "📊 1. 스트리밍 상태 확인..."
curl -s "$EXAMPLES_API/streaming-status" | jq '.'

sleep 2

# 사용자 이벤트 테스트
echo "👤 2. 사용자 이벤트 전송 테스트..."
curl -X POST "$EXAMPLES_API/user-events" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "event_type": "login",
    "page_url": "https://example.com/login",
    "metadata": {
      "device": "mobile",
      "location": "Seoul",
      "session_id": "session_789"
    }
  }' | jq '.'

sleep 2

# 페이지 방문 이벤트
echo "📄 3. 페이지 방문 이벤트 전송..."
curl -X POST "$EXAMPLES_API/user-events" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "event_type": "page_view",
    "page_url": "https://example.com/products/smartphone",
    "metadata": {
      "device": "mobile",
      "referrer": "https://google.com",
      "session_id": "session_789"
    }
  }' | jq '.'

sleep 2

# 상품 분석 이벤트 테스트
echo "📱 4. 상품 분석 이벤트 전송..."
curl -X POST "$EXAMPLES_API/product-analytics" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_smartphone_001",
    "action": "view",
    "user_id": "user_12345",
    "session_id": "session_789",
    "properties": {
      "category": "electronics",
      "brand": "Samsung",
      "price": 1200000,
      "rating": 4.5
    }
  }' | jq '.'

sleep 2

# 장바구니 추가 이벤트
echo "🛒 5. 장바구니 추가 이벤트 전송..."
curl -X POST "$EXAMPLES_API/product-analytics" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_smartphone_001",
    "action": "add_to_cart",
    "user_id": "user_12345",
    "session_id": "session_789",
    "properties": {
      "quantity": 1,
      "color": "black",
      "storage": "256GB"
    }
  }' | jq '.'

sleep 2

# 주문 이벤트 테스트
echo "💳 6. 주문 생성 이벤트 전송..."
curl -X POST "$EXAMPLES_API/order-events" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order_67890",
    "user_id": "user_12345",
    "status": "created",
    "items": [
      {
        "product_id": "prod_smartphone_001",
        "quantity": 1,
        "price": 1200000,
        "name": "Samsung Galaxy S24"
      }
    ],
    "total_amount": 1200000,
    "shipping_address": {
      "city": "Seoul",
      "district": "Gangnam-gu",
      "street": "Teheran-ro 123",
      "zipcode": "12345"
    }
  }' | jq '.'

sleep 2

# 결제 완료 이벤트
echo "✅ 7. 결제 완료 이벤트 전송..."
curl -X POST "$EXAMPLES_API/order-events" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order_67890",
    "user_id": "user_12345",
    "status": "paid",
    "items": [
      {
        "product_id": "prod_smartphone_001",
        "quantity": 1,
        "price": 1200000,
        "name": "Samsung Galaxy S24"
      }
    ],
    "total_amount": 1200000,
    "shipping_address": {
      "city": "Seoul",
      "district": "Gangnam-gu",
      "street": "Teheran-ro 123",
      "zipcode": "12345"
    }
  }' | jq '.'

sleep 2

# 배치 이벤트 처리 테스트
echo "📦 8. 배치 이벤트 처리 테스트..."
curl -X POST "$EXAMPLES_API/batch-events?topic=batch_test_events" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "event_001",
      "type": "log_entry",
      "message": "User login successful",
      "user_id": "user_001"
    },
    {
      "id": "event_002",
      "type": "log_entry",
      "message": "Product viewed",
      "user_id": "user_002",
      "product_id": "prod_002"
    },
    {
      "id": "event_003",
      "type": "log_entry",
      "message": "Order placed",
      "user_id": "user_003",
      "order_id": "order_003"
    }
  ]' | jq '.'

sleep 2

# 배송 시작 이벤트
echo "🚚 9. 배송 시작 이벤트 전송..."
curl -X POST "$EXAMPLES_API/order-events" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order_67890",
    "user_id": "user_12345",
    "status": "shipped",
    "items": [
      {
        "product_id": "prod_smartphone_001",
        "quantity": 1,
        "price": 1200000,
        "name": "Samsung Galaxy S24"
      }
    ],
    "total_amount": 1200000,
    "shipping_address": {
      "city": "Seoul",
      "district": "Gangnam-gu",
      "street": "Teheran-ro 123",
      "zipcode": "12345"
    }
  }' | jq '.'

sleep 2

# 구매 완료 이벤트 (상품 분석용)
echo "🎉 10. 구매 완료 분석 이벤트 전송..."
curl -X POST "$EXAMPLES_API/product-analytics" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_smartphone_001",
    "action": "purchase",
    "user_id": "user_12345",
    "session_id": "session_789",
    "properties": {
      "purchase_amount": 1200000,
      "payment_method": "credit_card",
      "discount_applied": false
    }
  }' | jq '.'

sleep 2

# 최종 상태 확인
echo "📊 11. 최종 스트리밍 상태 확인..."
curl -s "$EXAMPLES_API/streaming-status" | jq '.'

echo ""
echo "✅ Kafka 스트리밍 예제 API 테스트가 완료되었습니다!"
echo "🔍 Kafka UI에서 메시지 확인: http://localhost:8082"
echo "📈 Grafana 대시보드: http://localhost:3000 (admin/admin)"
echo "📊 Prometheus 메트릭: http://localhost:9090"