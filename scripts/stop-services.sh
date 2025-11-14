#!/bin/bash

# Stop all services
echo "Stopping all streaming services..."

# Stop Docker Compose services
docker-compose down

echo "All services stopped!"