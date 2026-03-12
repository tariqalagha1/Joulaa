from __future__ import annotations

from typing import Any, Dict

from ..tools.builtin.email_tool import EmailTool
from ..tools.builtin.notify_tool import NotifyTool
from ..tools.builtin.web_search_tool import WebSearchTool
from ..tools.registry import ToolRegistry
from .schemas import ExecutionStep

ALLOWED_TOOLS = {
    "default": ["web_search", "send_email", "notify_user"],
}


class AgentDispatcher:
    def __init__(self) -> None:
        self.registry = ToolRegistry()
        self.registry.register_tool(WebSearchTool())
        self.registry.register_tool(EmailTool())
        self.registry.register_tool(NotifyTool())

    async def dispatch_step(self, step: ExecutionStep) -> Dict[str, Any]:
        if step.action not in ALLOWED_TOOLS["default"]:
            return {
                "error": f"Tool '{step.action}' is not allowed",
                "step_id": step.step_id,
                "action": step.action,
            }

        tool = self.registry.get_tool(step.action)
        if tool:
            return await tool.execute(step.input_payload)

        return {
            "error": f"Tool '{step.action}' is not registered",
            "step_id": step.step_id,
            "action": step.action,
            "available_tools": self.registry.list_tools(),
        }
