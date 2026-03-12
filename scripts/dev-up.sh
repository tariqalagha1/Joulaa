#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${ROOT_DIR}/.tmp"
mkdir -p "${TMP_DIR}"

BACKEND_LOG="${TMP_DIR}/backend-dev.log"
FRONTEND_LOG="${TMP_DIR}/frontend-dev.log"
BACKEND_PID_FILE="${TMP_DIR}/backend-dev.pid"
FRONTEND_PID_FILE="${TMP_DIR}/frontend-dev.pid"

start_or_reuse() {
  local label="$1"
  local pid_file="$2"
  local log_file="$3"
  local cmd="$4"
  local port="$5"

  if [[ -f "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
    echo "${label} already running with PID $(cat "${pid_file}")"
    return
  fi

  if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "${label} appears to be already running (port ${port} is in use)"
    return
  fi

  nohup bash -lc "${cmd}" > "${log_file}" 2>&1 &
  local pid=$!
  echo "${pid}" > "${pid_file}"
  sleep 1

  if kill -0 "${pid}" 2>/dev/null; then
    echo "Started ${label} (PID ${pid})"
    return
  fi

  echo "Failed to start ${label}. Recent log output:"
  tail -n 30 "${log_file}" || true
  rm -f "${pid_file}"
  exit 1
}

start_or_reuse "backend on http://127.0.0.1:8002" \
  "${BACKEND_PID_FILE}" \
  "${BACKEND_LOG}" \
  "cd '${ROOT_DIR}/backend' && venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8002" \
  "8002"

start_or_reuse "frontend on http://127.0.0.1:5174" \
  "${FRONTEND_PID_FILE}" \
  "${FRONTEND_LOG}" \
  "cd '${ROOT_DIR}/frontend' && npm run dev -- --host 127.0.0.1 --port 5174" \
  "5174"

echo ""
echo "Frontend: http://127.0.0.1:5174"
echo "Backend:  http://127.0.0.1:8002"
echo "Logs:"
echo "  ${FRONTEND_LOG}"
echo "  ${BACKEND_LOG}"
