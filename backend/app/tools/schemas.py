from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_name: str = Field(..., description="Registered tool name")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Tool input payload")
