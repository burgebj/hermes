#!/bin/bash
# Jaeger all-in-one for Hermes-Agent distributed tracing
# Usage: ./scripts/start_jaeger.sh
#
# Prerequisites:
#   - Docker installed and running
#   - Docker network accessible
#
# Endpoints after startup:
#   Jaeger UI:         http://localhost:16686
#   OTLP gRPC:         localhost:4317
#   OTLP HTTP:         localhost:4318
#
# Environment variables to set in your shell before running Hermes:
#   export OTEL_EXPORTER_ENDPOINT=http://localhost:4317
#   export OTEL_EXPORTER_TYPE=otlp_grpc
#   export OTEL_SERVICE_NAME=hermes-agent

set -e

echo "Starting Jaeger all-in-one for Hermes-Agent distributed tracing..."
echo ""
echo "Endpoints:"
echo "  Jaeger UI:    http://localhost:16686"
echo "  OTLP gRPC:    localhost:4317"
echo "  OTLP HTTP:    localhost:4318"
echo ""
echo "To trace Hermes-Agent, set these environment variables:"
echo "  export OTEL_EXPORTER_ENDPOINT=http://localhost:4317"
echo "  export OTEL_EXPORTER_TYPE=otlp_grpc"
echo "  export OTEL_SERVICE_NAME=hermes-agent"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH."
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running."
    echo "Start Docker and try again."
    exit 1
fi

# Check if Jaeger container is already running
if docker ps --format '{{.Names}}' | grep -q "^hermes-jaeger$"; then
    echo "Jaeger container 'hermes-jaeger' is already running."
    echo "Open http://localhost:16686 to view traces."
    exit 0
fi

# Stop any existing hermes-jaeger container
if docker ps -a --format '{{.Names}}' | grep -q "^hermes-jaeger$"; then
    echo "Removing existing hermes-jaeger container..."
    docker rm -f hermes-jaeger > /dev/null 2>&1 || true
fi

echo "Starting Jaeger all-in-one..."
docker run --rm \
  --name hermes-jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -e COLLECTOR_OTLP_ENABLED=true \
  jaegertracing/all-in-one:1.52 &

JAEGER_PID=$!

echo ""
echo "Jaeger is starting up (PID: $JAEGER_PID)..."
echo "Wait a few seconds for the UI to be ready, then open:"
echo "  http://localhost:16686"
echo ""
echo "Press Ctrl+C to stop Jaeger."
echo ""

# Wait for the process
wait $JAEGER_PID
