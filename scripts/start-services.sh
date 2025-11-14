#!/bin/bash

# Kafka 스트리밍 프로젝트 시작 스크립트
set -e

echo "🚀 Kafka 스트리밍 프로젝트를 시작합니다..."

# .env 파일 생성 (없는 경우)
if [ ! -f .env ]; then
    echo "📝 .env 파일을 .env.example에서 복사합니다..."
    cp .env.example .env
fi

# Docker Compose로 모든 서비스 시작
echo "🐳 Docker 서비스들을 시작하는 중..."
docker-compose up -d

echo "⏳ 서비스들이 준비될 때까지 잠시 기다리는 중..."
sleep 30

# 서비스 상태 확인
echo "🔍 서비스 상태 확인 중..."
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔧 서비스 헬스체크를 진행합니다..."

# Kafka 헬스체크
echo "📡 Kafka 상태 확인..."
timeout 60 bash -c 'until docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; do echo "Kafka를 기다리는 중..."; sleep 5; done'
echo "✅ Kafka 준비 완료"

# PostgreSQL 헬스체크
echo "🐘 PostgreSQL 상태 확인..."
timeout 60 bash -c 'until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do echo "PostgreSQL을 기다리는 중..."; sleep 5; done'
echo "✅ PostgreSQL 준비 완료"

# Redis 헬스체크
echo "🔴 Redis 상태 확인..."
timeout 60 bash -c 'until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do echo "Redis를 기다리는 중..."; sleep 5; done'
echo "✅ Redis 준비 완료"

# LocalStack 헬스체크
echo "☁️  LocalStack 상태 확인..."
timeout 60 bash -c 'until curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; do echo "LocalStack을 기다리는 중..."; sleep 5; done'
echo "✅ LocalStack 준비 완료"

# FastAPI 애플리케이션 헬스체크
echo "🐍 FastAPI 애플리케이션 상태 확인..."
timeout 60 bash -c 'until curl -s http://localhost:8888/health > /dev/null 2>&1; do echo "FastAPI 애플리케이션을 기다리는 중..."; sleep 5; done'
echo "✅ FastAPI 애플리케이션 준비 완료"

# Kafka UI 헬스체크
echo "🖥️  Kafka UI 상태 확인..."
timeout 60 bash -c 'until curl -s http://localhost:8082 > /dev/null 2>&1; do echo "Kafka UI를 기다리는 중..."; sleep 5; done'
echo "✅ Kafka UI 준비 완료"

echo ""
echo "🎉 모든 서비스가 성공적으로 시작되었습니다!"
echo ""
echo "📌 사용 가능한 서비스들:"
echo "   🌐 FastAPI 애플리케이션: http://localhost:8888"
echo "   📖 API 문서 (Swagger): http://localhost:8888/docs"
echo "   🔍 Kafka UI: http://localhost:8082"
echo "   📊 Grafana: http://localhost:3000 (admin/admin)"
echo "   📈 Prometheus: http://localhost:9090"
echo "   🗄️  PostgreSQL: localhost:5433 (postgres/postgres)"
echo "   🔴 Redis: localhost:6380"
echo "   ☁️  LocalStack: http://localhost:4566"
echo ""
echo "🧪 예제 API 테스트 실행:"
echo "   ./scripts/test-examples.sh"
echo ""
echo "🏃‍♂️ 실시간 로그 보기:"
echo "   docker-compose logs -f streaming-app"
echo ""
echo "🛑 서비스 중지:"
echo "   docker-compose down"