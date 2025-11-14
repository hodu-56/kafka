"""
Kafka 스트리밍 사용 예제 - FastAPI Router
실제 비즈니스 시나리오에서 Kafka가 어떻게 동작하는지 보여주는 예제들
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
import asyncio

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()


# =============================================================================
# Pydantic Models
# =============================================================================

class UserEvent(BaseModel):
    """사용자 이벤트 모델"""
    user_id: str = Field(..., description="사용자 ID")
    event_type: str = Field(..., description="이벤트 타입: login, logout, page_view, purchase")
    page_url: Optional[str] = Field(None, description="페이지 URL (page_view인 경우)")
    product_id: Optional[str] = Field(None, description="상품 ID (purchase인 경우)")
    amount: Optional[float] = Field(None, description="구매 금액 (purchase인 경우)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class OrderEvent(BaseModel):
    """주문 이벤트 모델"""
    order_id: str = Field(..., description="주문 ID")
    user_id: str = Field(..., description="사용자 ID")
    status: str = Field(..., description="주문 상태: created, paid, shipped, delivered, cancelled")
    items: List[Dict[str, Any]] = Field(..., description="주문 상품 목록")
    total_amount: float = Field(..., description="총 주문 금액")
    shipping_address: Dict[str, str] = Field(..., description="배송 주소")


class ProductAnalytics(BaseModel):
    """상품 분석 이벤트 모델"""
    product_id: str = Field(..., description="상품 ID")
    action: str = Field(..., description="액션: view, add_to_cart, purchase, review")
    user_id: Optional[str] = Field(None, description="사용자 ID (로그인한 경우)")
    session_id: str = Field(..., description="세션 ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="상품 속성")


class EventResponse(BaseModel):
    """이벤트 처리 응답"""
    success: bool
    message: str
    event_id: str
    kafka_result: Optional[Dict[str, Any]] = None
    processing_time_ms: float


# =============================================================================
# 1. 사용자 행동 추적 API - 실시간 이벤트 스트리밍
# =============================================================================

@router.post("/user-events", response_model=EventResponse, summary="사용자 이벤트 추적")
async def track_user_event(
    event: UserEvent,
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> EventResponse:
    """
    사용자 행동을 추적하고 Kafka로 실시간 스트리밍

    **언제 사용되나요?**
    - 사용자가 웹사이트에 로그인할 때
    - 특정 페이지를 방문할 때
    - 상품을 구매할 때
    - 로그아웃할 때

    **Kafka 토픽**: `user_events`
    **용도**: 실시간 사용자 분석, 개인화 추천, A/B 테스트
    """
    start_time = datetime.now()
    event_id = str(uuid.uuid4())

    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        # 이벤트 데이터 준비
        event_data = {
            "event_id": event_id,
            "user_id": event.user_id,
            "event_type": event.event_type,
            "timestamp": datetime.now().isoformat(),
            "page_url": event.page_url,
            "product_id": event.product_id,
            "amount": event.amount,
            "metadata": event.metadata,
            "source": "web_app",
            "version": "1.0"
        }

        # Kafka로 메시지 전송
        kafka_result = await kafka_service.produce_message(
            topic="user_events",
            key=event.user_id,  # 같은 사용자의 이벤트는 같은 파티션으로
            value=event_data,
            headers={
                "event_type": event.event_type,
                "source": "user_tracking_api",
                "content_type": "application/json"
            }
        )

        # 백그라운드에서 추가 처리 (세션 분석, 추천 시스템 업데이트 등)
        background_tasks.add_task(
            process_user_event_analytics,
            event_data,
            kafka_service
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            "User event tracked successfully",
            event_id=event_id,
            user_id=event.user_id,
            event_type=event.event_type,
            kafka_partition=kafka_result.get("partition"),
            kafka_offset=kafka_result.get("offset")
        )

        return EventResponse(
            success=True,
            message=f"User event '{event.event_type}' tracked successfully",
            event_id=event_id,
            kafka_result=kafka_result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error("Failed to track user event", error=str(e), event_id=event_id)
        raise HTTPException(status_code=500, detail=f"Failed to track event: {str(e)}")


# =============================================================================
# 2. 주문 처리 API - 주문 상태 변경 스트리밍
# =============================================================================

@router.post("/order-events", response_model=EventResponse, summary="주문 이벤트 추적")
async def track_order_event(
    order: OrderEvent,
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> EventResponse:
    """
    주문 상태 변경을 추적하고 Kafka로 스트리밍

    **언제 사용되나요?**
    - 새 주문이 생성될 때
    - 결제가 완료될 때
    - 상품이 출고될 때
    - 배송이 완료될 때
    - 주문이 취소될 때

    **Kafka 토픽**: `order_events`
    **용도**: 주문 상태 추적, 재고 관리, 배송 알림, 매출 분석
    """
    start_time = datetime.now()
    event_id = str(uuid.uuid4())

    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        # 주문 이벤트 데이터 준비
        order_data = {
            "event_id": event_id,
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "timestamp": datetime.now().isoformat(),
            "items": order.items,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "item_count": len(order.items),
            "source": "order_management_system",
            "version": "1.0"
        }

        # Kafka로 메시지 전송
        kafka_result = await kafka_service.produce_message(
            topic="order_events",
            key=order.order_id,  # 같은 주문의 이벤트는 순서 보장
            value=order_data,
            headers={
                "order_status": order.status,
                "user_id": order.user_id,
                "source": "order_api",
                "content_type": "application/json"
            }
        )

        # 상태별 후속 처리
        if order.status == "paid":
            background_tasks.add_task(
                process_payment_completion,
                order_data,
                kafka_service
            )
        elif order.status == "shipped":
            background_tasks.add_task(
                send_shipping_notification,
                order_data,
                kafka_service
            )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            "Order event tracked successfully",
            event_id=event_id,
            order_id=order.order_id,
            status=order.status,
            kafka_partition=kafka_result.get("partition"),
            kafka_offset=kafka_result.get("offset")
        )

        return EventResponse(
            success=True,
            message=f"Order event '{order.status}' tracked successfully",
            event_id=event_id,
            kafka_result=kafka_result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error("Failed to track order event", error=str(e), event_id=event_id)
        raise HTTPException(status_code=500, detail=f"Failed to track order event: {str(e)}")


# =============================================================================
# 3. 상품 분석 API - 상품 관련 이벤트 스트리밍
# =============================================================================

@router.post("/product-analytics", response_model=EventResponse, summary="상품 분석 추적")
async def track_product_analytics(
    analytics: ProductAnalytics,
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> EventResponse:
    """
    상품 관련 사용자 행동을 추적하고 분석용 데이터 스트리밍

    **언제 사용되나요?**
    - 상품 페이지를 조회할 때
    - 장바구니에 상품을 추가할 때
    - 상품을 구매할 때
    - 상품 리뷰를 작성할 때

    **Kafka 토픽**: `product_analytics`
    **용도**: 인기 상품 분석, 추천 시스템, 재고 예측, 마케팅 분석
    """
    start_time = datetime.now()
    event_id = str(uuid.uuid4())

    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        # 상품 분석 데이터 준비
        analytics_data = {
            "event_id": event_id,
            "product_id": analytics.product_id,
            "action": analytics.action,
            "user_id": analytics.user_id,
            "session_id": analytics.session_id,
            "timestamp": datetime.now().isoformat(),
            "properties": analytics.properties,
            "is_logged_in": analytics.user_id is not None,
            "source": "product_tracking",
            "version": "1.0"
        }

        # Kafka로 메시지 전송
        kafka_result = await kafka_service.produce_message(
            topic="product_analytics",
            key=analytics.product_id,  # 같은 상품의 분석 데이터는 같은 파티션으로
            value=analytics_data,
            headers={
                "action": analytics.action,
                "product_id": analytics.product_id,
                "source": "product_analytics_api",
                "content_type": "application/json"
            }
        )

        # 액션별 후속 처리
        if analytics.action == "purchase":
            background_tasks.add_task(
                update_product_popularity,
                analytics_data,
                kafka_service
            )
        elif analytics.action == "view":
            background_tasks.add_task(
                update_view_statistics,
                analytics_data,
                kafka_service
            )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            "Product analytics tracked successfully",
            event_id=event_id,
            product_id=analytics.product_id,
            action=analytics.action,
            kafka_partition=kafka_result.get("partition"),
            kafka_offset=kafka_result.get("offset")
        )

        return EventResponse(
            success=True,
            message=f"Product analytics '{analytics.action}' tracked successfully",
            event_id=event_id,
            kafka_result=kafka_result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error("Failed to track product analytics", error=str(e), event_id=event_id)
        raise HTTPException(status_code=500, detail=f"Failed to track analytics: {str(e)}")


# =============================================================================
# 4. 배치 이벤트 처리 API - 대용량 데이터 한번에 스트리밍
# =============================================================================

@router.post("/batch-events", summary="배치 이벤트 처리")
async def process_batch_events(
    events: List[Dict[str, Any]],
    topic: str,
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    대용량 이벤트를 배치로 처리하고 Kafka로 스트리밍

    **언제 사용되나요?**
    - 일일 배치 작업으로 로그 데이터를 처리할 때
    - 외부 시스템에서 대량의 데이터를 받을 때
    - 데이터 마이그레이션 작업을 할 때

    **용도**: ETL 작업, 데이터 동기화, 대용량 분석 작업
    """
    start_time = datetime.now()
    batch_id = str(uuid.uuid4())

    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            raise HTTPException(status_code=503, detail="Kafka service not available")

        # 배치 처리용 메시지 준비
        batch_messages = []
        for i, event in enumerate(events):
            event["batch_id"] = batch_id
            event["batch_index"] = i
            event["batch_size"] = len(events)
            event["timestamp"] = datetime.now().isoformat()

            batch_messages.append({
                "value": event,
                "key": event.get("id", f"batch_{batch_id}_{i}"),
                "headers": {
                    "batch_id": batch_id,
                    "batch_index": str(i),
                    "source": "batch_processing_api"
                }
            })

        # Kafka로 배치 전송
        results = await kafka_service.batch_produce(batch_messages, topic)

        successful_count = len(results)
        failed_count = len(events) - successful_count

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            "Batch events processed",
            batch_id=batch_id,
            total_events=len(events),
            successful=successful_count,
            failed=failed_count,
            topic=topic
        )

        return {
            "success": True,
            "batch_id": batch_id,
            "total_events": len(events),
            "successful_events": successful_count,
            "failed_events": failed_count,
            "processing_time_ms": processing_time,
            "kafka_results": results[:10]  # 처음 10개만 반환
        }

    except Exception as e:
        logger.error("Failed to process batch events", error=str(e), batch_id=batch_id)
        raise HTTPException(status_code=500, detail=f"Failed to process batch: {str(e)}")


# =============================================================================
# 5. 실시간 상태 확인 API
# =============================================================================

@router.get("/streaming-status", summary="스트리밍 상태 확인")
async def get_streaming_status(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Kafka 스트리밍 상태 확인
    현재 Kafka 연결 상태, 처리된 메시지 수, 토픽 정보 등을 반환
    """
    try:
        kafka_service = getattr(request.app.state, 'kafka_service', None)
        if not kafka_service:
            return {"status": "unavailable", "message": "Kafka service not available"}

        # Kafka 상태 및 메트릭 조회
        is_healthy = await kafka_service.is_healthy()
        metrics = await kafka_service.get_metrics()

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "is_running": kafka_service.is_running,
            "metrics": metrics,
            "topics": {
                "user_events": "사용자 행동 추적",
                "order_events": "주문 상태 변경",
                "product_analytics": "상품 분석 데이터",
                "user_sessions": "세션 분석",
                "inventory_events": "재고 변동",
                "notifications": "알림 이벤트",
                "product_popularity": "상품 인기도",
                "product_views": "상품 조회수"
            }
        }

    except Exception as e:
        logger.error("Failed to get streaming status", error=str(e))
        return {"status": "error", "message": str(e)}


@router.get("/topics/{topic}/recent-messages", summary="최근 메시지 조회")
async def get_recent_messages(
    topic: str,
    limit: int = 10,
    request: Request = None,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    특정 토픽의 최근 메시지 조회 (개발/디버깅 용도)
    """
    try:
        # 실제 구현에서는 Kafka Consumer를 사용해서 최근 메시지를 조회
        # 여기서는 예제용 응답을 반환
        return {
            "topic": topic,
            "recent_messages": [
                {
                    "offset": i,
                    "timestamp": datetime.now().isoformat(),
                    "key": f"sample_key_{i}",
                    "value": {"sample": f"message_{i}"}
                }
                for i in range(limit)
            ],
            "message": f"최근 {limit}개의 메시지 (실제 구현 필요)"
        }

    except Exception as e:
        logger.error("Failed to get recent messages", error=str(e), topic=topic)
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


# =============================================================================
# 백그라운드 처리 함수들
# =============================================================================

async def process_user_event_analytics(event_data: Dict[str, Any], kafka_service):
    """사용자 이벤트 분석 처리"""
    try:
        # 세션 분석용 이벤트 생성
        session_data = {
            "user_id": event_data["user_id"],
            "session_id": event_data.get("metadata", {}).get("session_id"),
            "event_type": "session_update",
            "last_activity": event_data["timestamp"],
            "source": "session_analytics"
        }

        await kafka_service.produce_message(
            topic="user_sessions",
            key=event_data["user_id"],
            value=session_data
        )

        logger.info("Session analytics processed", user_id=event_data["user_id"])

    except Exception as e:
        logger.error("Failed to process user event analytics", error=str(e))


async def process_payment_completion(order_data: Dict[str, Any], kafka_service):
    """결제 완료 처리"""
    try:
        # 재고 차감 이벤트 생성
        for item in order_data["items"]:
            inventory_event = {
                "product_id": item["product_id"],
                "quantity_sold": item["quantity"],
                "order_id": order_data["order_id"],
                "timestamp": datetime.now().isoformat(),
                "event_type": "inventory_decrease",
                "source": "payment_processor"
            }

            await kafka_service.produce_message(
                topic="inventory_events",
                key=item["product_id"],
                value=inventory_event
            )

        logger.info("Payment completion processed", order_id=order_data["order_id"])

    except Exception as e:
        logger.error("Failed to process payment completion", error=str(e))


async def send_shipping_notification(order_data: Dict[str, Any], kafka_service):
    """배송 알림 처리"""
    try:
        notification_event = {
            "user_id": order_data["user_id"],
            "order_id": order_data["order_id"],
            "type": "shipping_notification",
            "message": f"주문 {order_data['order_id']}이 발송되었습니다.",
            "timestamp": datetime.now().isoformat(),
            "source": "shipping_processor"
        }

        await kafka_service.produce_message(
            topic="notifications",
            key=order_data["user_id"],
            value=notification_event
        )

        logger.info("Shipping notification sent", order_id=order_data["order_id"])

    except Exception as e:
        logger.error("Failed to send shipping notification", error=str(e))


async def update_product_popularity(analytics_data: Dict[str, Any], kafka_service):
    """상품 인기도 업데이트"""
    try:
        popularity_event = {
            "product_id": analytics_data["product_id"],
            "action": "purchase",
            "timestamp": analytics_data["timestamp"],
            "user_id": analytics_data.get("user_id"),
            "source": "popularity_tracker"
        }

        await kafka_service.produce_message(
            topic="product_popularity",
            key=analytics_data["product_id"],
            value=popularity_event
        )

        logger.info("Product popularity updated", product_id=analytics_data["product_id"])

    except Exception as e:
        logger.error("Failed to update product popularity", error=str(e))


async def update_view_statistics(analytics_data: Dict[str, Any], kafka_service):
    """상품 조회 통계 업데이트"""
    try:
        view_event = {
            "product_id": analytics_data["product_id"],
            "timestamp": analytics_data["timestamp"],
            "session_id": analytics_data["session_id"],
            "user_id": analytics_data.get("user_id"),
            "source": "view_tracker"
        }

        await kafka_service.produce_message(
            topic="product_views",
            key=analytics_data["product_id"],
            value=view_event
        )

        logger.info("View statistics updated", product_id=analytics_data["product_id"])

    except Exception as e:
        logger.error("Failed to update view statistics", error=str(e))