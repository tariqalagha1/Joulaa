#!/usr/bin/env python3
"""Minimal smoke test for Joulaa backend endpoints."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")


def request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
) -> tuple[int, Any]:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, parse_body(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, parse_body(body)
    except Exception as exc:  # pragma: no cover - smoke script fallback
        return 0, {"error": str(exc)}


def parse_body(body: str) -> Any:
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return body


def row(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
    }


def format_body(body: Any) -> str:
    if isinstance(body, dict):
        if "detail" in body:
            return str(body["detail"])
        if "status" in body:
            return str(body["status"])
        return json.dumps(body, ensure_ascii=True)[:120]
    if body is None:
        return ""
    return str(body)[:120]


def main() -> int:
    results: list[dict[str, str]] = []
    token: str | None = None
    login_status: int | None = None
    login_body: Any = None

    status, body = request("GET", "/health")
    results.append(row("GET /health", status == 200, f"{status} {format_body(body)}"))

    if EMAIL and PASSWORD:
        login_status, login_body = request(
            "POST",
            "/api/v1/auth/login",
            {"email_or_username": EMAIL, "password": PASSWORD},
        )
        token = login_body.get("access_token") if isinstance(login_body, dict) else None
        passed = login_status == 200 and bool(token)
        detail = f"{login_status} {'access_token present' if token else format_body(login_body)}"
        results.append(row("POST /api/v1/auth/login (real creds)", passed, detail))
    else:
        login_status, login_body = request(
            "POST",
            "/api/v1/auth/login",
            {"email_or_username": "smoke-test-invalid-user", "password": "badpass123"},
        )
        passed = login_status == 401
        results.append(
            row(
                "POST /api/v1/auth/login (invalid creds)",
                passed,
                f"{login_status} {format_body(login_body)}",
            )
        )

    status, body = request("GET", "/api/v1/auth/me")
    results.append(row("GET /api/v1/auth/me (no token)", status == 401, f"{status} {format_body(body)}"))

    if token:
        status, body = request("GET", "/api/v1/auth/me", token=token)
        results.append(row("GET /api/v1/auth/me (with token)", status == 200, f"{status} {format_body(body)}"))
    else:
        results.append(row("GET /api/v1/auth/me (with token)", True, "SKIPPED no valid login credentials supplied"))

    status, body = request("GET", "/api/v1/agents/")
    results.append(row("GET /api/v1/agents/ (no token)", status == 401, f"{status} {format_body(body)}"))

    status, body = request("GET", "/api/v1/conversations/")
    results.append(row("GET /api/v1/conversations/ (no token)", status == 401, f"{status} {format_body(body)}"))

    name_width = max(len(item["name"]) for item in results)
    status_width = 4

    print(f"Smoke test target: {BASE_URL}")
    if EMAIL and PASSWORD:
        print("Login mode: real credentials from EMAIL/PASSWORD")
    else:
        print("Login mode: invalid-credential safety check")
    print()
    print(f"{'Endpoint'.ljust(name_width)}  {'Result'.ljust(status_width)}  Detail")
    print(f"{'-' * name_width}  {'-' * status_width}  {'-' * 40}")
    for item in results:
        print(f"{item['name'].ljust(name_width)}  {item['status'].ljust(status_width)}  {item['detail']}")

    failures = [item for item in results if item["status"] == "FAIL"]
    print()
    print(f"Summary: {len(results) - len(failures)} passed, {len(failures)} failed")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
