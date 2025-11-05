#!/bin/bash

# Initialize database with migrations
echo "Waiting for database to be ready..."
sleep 5

echo "Creating initial migration..."
alembic revision --autogenerate -m "Initial migration"

echo "Applying migrations..."
alembic upgrade head

echo "Database initialization complete!"
