from __future__ import annotations

from typing import Any, Dict

from ..base_tool import BaseTool


class EmailTool(BaseTool):
    name = "send_email"
    description = "Mock email delivery tool"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        context = payload.get("context", {})
        previous_results = list(context.values())
        return {
            "tool": self.name,
            "status": "mocked",
            "message": "Email queued (mock)",
            "payload": payload,
            "context": context,
            "previous_results": previous_results,
        }
