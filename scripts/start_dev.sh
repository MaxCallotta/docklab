#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${1:-127.0.0.1}"
PORT="${2:-8000}"

echo "[1/2] 启动 FastAPI 后端 (http://${HOST}:${PORT})"
(
  cd "$ROOT/backend"
  nohup python -m uvicorn app.main:app --host "$HOST" --port "$PORT" > "$ROOT/pax-backend.log" 2>&1 &
  echo $! > "$ROOT/pax-backend.pid"
)

echo "[2/2] 启动 Vite 前端 (http://localhost:5173)"
cd "$ROOT/frontend"
npm run dev
