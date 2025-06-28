#!/bin/bash

# Kimi-Dev-72B Cloud Browser Service Startup Script
echo "🚀 Starting Kimi-Dev-72B Cloud Browser Service..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

# Build and start services
echo "📦 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:5000"
    echo "📊 Health Check: http://localhost:5000/api/v1/health"
    echo ""
    echo "📋 Default Admin Credentials:"
    echo "   Email: admin@secure-kimi.local"
    echo "   Password: SecureKimi2024!"
    echo ""
    echo "📖 View logs: docker-compose logs -f"
    echo "⏹️  Stop services: docker-compose down"
else
    echo "❌ Failed to start some services. Check logs:"
    docker-compose logs
fi
