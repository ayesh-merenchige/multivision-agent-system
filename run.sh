#!/usr/bin/env bash
# Start the Multivisions backend (8000) and frontend (3000) together.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# --- ensure .env exists -----------------------------------------------------
if [ ! -f .env ]; then
  echo "No .env found — creating one from .env.example."
  echo "⚠️  Edit .env and set your GEMINI_API_KEY before running."
  cp .env.example .env
fi

# --- backend ----------------------------------------------------------------
echo "Starting backend on http://localhost:8000 …"
(cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

# --- frontend ---------------------------------------------------------------
echo "Starting frontend on http://localhost:3000 …"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

cleanup() {
  echo "Shutting down…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo "Both services starting. Press Ctrl+C to stop."
wait
