#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${ROOT_DIR}/.tmp"
BACKEND_PID_FILE="${TMP_DIR}/backend-dev.pid"
FRONTEND_PID_FILE="${TMP_DIR}/frontend-dev.pid"

stop_pid_file() {
  local label="$1"
  local pid_file="$2"

  if [[ ! -f "${pid_file}" ]]; then
    echo "${label}: no PID file"
    return
  fi

  local pid
  pid="$(cat "${pid_file}")"

  if kill -0 "${pid}" 2>/dev/null; then
    kill "${pid}" 2>/dev/null || true
    sleep 1
    if kill -0 "${pid}" 2>/dev/null; then
      kill -9 "${pid}" 2>/dev/null || true
    fi
    echo "${label}: stopped PID ${pid}"
  else
    echo "${label}: PID ${pid} not running"
  fi

  rm -f "${pid_file}"
}

stop_pid_file "Backend" "${BACKEND_PID_FILE}"
stop_pid_file "Frontend" "${FRONTEND_PID_FILE}"
