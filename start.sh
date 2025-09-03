#!/bin/bash

# They Might Say - Startup Script
# This script helps you get the system running quickly

set -e

echo "🚀 They Might Say - Starting System"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. You may want to customize it."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p database/backups

# Pull latest images
echo "📦 Pulling Docker images..."
docker-compose pull

# Build services
echo "🔨 Building services..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
services=("postgres" "redis" "minio" "backend")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose ps | grep -q "${service}.*healthy"; then
        echo "✅ $service is healthy"
    else
        echo "⚠️  $service is not healthy yet"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo ""
    echo "🎉 System is ready!"
    echo "=================================="
    echo "📱 Frontend:     http://localhost:3000"
    echo "🔧 Backend API:  http://localhost:8000"
    echo "📚 API Docs:     http://localhost:8000/docs"
    echo "🗄️  MinIO:       http://localhost:9001"
    echo ""
    echo "🔑 Demo Login:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs:     docker-compose logs -f"
    echo "   Stop system:   docker-compose down"
    echo "   Restart:       docker-compose restart"
    echo "   Reset data:    docker-compose down -v"
else
    echo ""
    echo "⚠️  Some services are not healthy yet."
    echo "   Run 'docker-compose logs' to check for issues."
    echo "   Services may take a few more minutes to start."
fi

echo ""
echo "🔧 For troubleshooting, check the logs:"
echo "   docker-compose logs -f"