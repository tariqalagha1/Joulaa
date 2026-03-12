from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    request_id: str = Field(..., description="Unique orchestration request identifier")
    objective: str = Field(..., description="High-level goal to execute")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional execution context")
    max_steps: Optional[int] = Field(default=None, ge=1, description="Optional per-request step cap")


class ExecutionStep(BaseModel):
    step_id: str
    agent_type: str
    action: str
    input_payload: Dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    plan_id: str
    request_id: str
    steps: List[ExecutionStep] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    request_id: str
    plan_id: str
    status: Literal["success", "failed", "partial"]
    step_results: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
