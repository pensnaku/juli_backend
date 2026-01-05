#!/bin/bash
set -e

# Juli Backend Deployment Script
# Run this on the DigitalOcean droplet to deploy latest changes

APP_DIR="/opt/juli_backend"
COMPOSE_FILE="docker-compose.prod.yml"

echo "=== Juli Backend Deployment ==="
echo "Started at: $(date)"

# Navigate to app directory
cd "$APP_DIR"

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Build and restart containers
echo "Building and starting containers..."
docker compose -f "$COMPOSE_FILE" build
docker compose -f "$COMPOSE_FILE" up -d

# Wait for database to be ready
echo "Waiting for database..."
sleep 5

# Run database migrations
echo "Running database migrations..."
docker compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head

# Health check
echo "Running health check..."
sleep 3
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "Health check passed!"
else
    echo "Warning: Health check failed. Check logs with: docker compose -f $COMPOSE_FILE logs api"
fi

# Cleanup old images
echo "Cleaning up old Docker images..."
docker image prune -f

echo "=== Deployment Complete ==="
echo "Finished at: $(date)"
