from __future__ import annotations

from typing import Any, Dict


class ToolExecutor:
    async def execute_tool(self, action: str, payload: dict) -> Dict[str, Any]:
        return {
            "action": action,
            "status": "mocked",
            "result": {
                "message": "placeholder tool execution result",
                "payload": payload,
            },
        }
