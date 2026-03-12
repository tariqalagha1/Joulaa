from __future__ import annotations

from typing import Any, Dict

from ..base_tool import BaseTool


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Example builtin web search tool placeholder"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query = str(payload.get("query", "")).strip()
        context = payload.get("context", {})
        previous_results = list(context.values())
        return {
            "tool": self.name,
            "status": "mocked",
            "query": query,
            "results": [],
            "message": "Replace with real web search integration.",
            "context": context,
            "previous_results": previous_results,
        }
