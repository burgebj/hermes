#!/bin/bash
# Start vLLM OpenAI-compatible server for DeepSeek-V4-Flash
# Uses docker with GPU passthrough
#
# Usage:
#   ./run_vllm_deepseekv4.sh          # run in foreground (Ctrl+C to stop)
#   ./run_vllm_deepseekv4.sh -d       # run in background (detached)
#   ./run_vllm_deepseekv4.sh -s       # show server logs (for -d mode)
#   ./run_vllm_deepseekv4.sh -k       # kill the running container

set -euo pipefail

CONTAINER_NAME="vllm-deepseekv4"
IMAGE="vllm/vllm-openai:latest"
MODEL_PATH="/home/jianliu/work/models/deepseekv4_flash"
HOST_PORT=8000

# --- functions ---

start_foreground() {
  echo "Starting vLLM server (foreground)..."
  echo "Container: $CONTAINER_NAME"
  echo "Model: $MODEL_PATH"
  echo "Port: $HOST_PORT"
  echo "Press Ctrl+C to stop."
  echo ""

  docker run --rm \
    --name "$CONTAINER_NAME" \
    --gpus all \
    --privileged --ipc=host \
    -p "$HOST_PORT:8000" \
    -v "$MODEL_PATH:/model" \
    -e VLLM_ENGINE_READY_TIMEOUT_S=3600 \
    "$IMAGE" /model \
    --host 0.0.0.0 \
    --port 8000 \
    --trust-remote-code \
    --kv-cache-dtype fp8 \
    --block-size 256 \
    --enable-expert-parallel \
    --data-parallel-size 4 \
    --compilation-config '{"cudagraph_mode":"FULL_AND_PIECEWISE", "custom_ops":["all"]}' \
    --tokenizer-mode deepseek_v4 \
    --tool-call-parser deepseek_v4 \
    --enable-auto-tool-choice \
    --reasoning-parser deepseek_v4
}

start_detached() {
  echo "Starting vLLM server (detached)..."
  docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

  docker run -d \
    --name "$CONTAINER_NAME" \
    --gpus all \
    --privileged --ipc=host \
    -p "$HOST_PORT:8000" \
    -v "$MODEL_PATH:/model" \
    -e VLLM_ENGINE_READY_TIMEOUT_S=3600 \
    "$IMAGE" /model \
    --host 0.0.0.0 \
    --port 8000 \
    --trust-remote-code \
    --kv-cache-dtype fp8 \
    --block-size 256 \
    --enable-expert-parallel \
    --data-parallel-size 4 \
    --compilation-config '{"cudagraph_mode":"FULL_AND_PIECEWISE", "custom_ops":["all"]}' \
    --tokenizer-mode deepseek_v4 \
    --tool-call-parser deepseek_v4 \
    --enable-auto-tool-choice \
    --reasoning-parser deepseek_v4

  echo ""
  echo "Container started: $CONTAINER_NAME"
  echo "Watch logs: docker logs -f $CONTAINER_NAME"
  echo "Test API:   curl http://localhost:$HOST_PORT/v1/chat/completions ..."
}

show_logs() {
  docker logs -f "$CONTAINER_NAME"
}

kill_container() {
  echo "Stopping container $CONTAINER_NAME..."
  docker rm -f "$CONTAINER_NAME" 2>/dev/null && echo "Stopped." || echo "Container not running."
}

# --- dispatch ---

if ! docker info >/dev/null 2>&1; then
  echo "docker requires sudo, re-running with sudo..."
  exec sudo -E "$0" "$@"
fi

case "${1:-}" in
  -d|--detach)
    start_detached
    ;;
  -s|--logs)
    show_logs
    ;;
  -k|--kill)
    kill_container
    ;;
  -h|--help)
    echo "Usage: $0 [-d | -s | -k]"
    echo "  (no args)   Run in foreground"
    echo "  -d, --detach  Run in background (detached)"
    echo "  -s, --logs    Tail server logs (for -d mode)"
    echo "  -k, --kill    Stop the server container"
    echo "  -h, --help    Show this help"
    ;;
  *)
    start_foreground
    ;;
esac
