from __future__ import annotations

from .schemas import ExecutionPlan, ExecutionRequest, ExecutionStep


class Planner:
    async def create_plan(self, request: ExecutionRequest) -> ExecutionPlan:
        objective_text = request.objective.lower()
        steps = []

        if "search" in objective_text:
            steps.append(
                ExecutionStep(
                    step_id=f"step-{len(steps) + 1}",
                    agent_type="tool",
                    action="web_search",
                    input_payload={
                        "query": request.objective,
                        "context": request.context,
                    },
                )
            )

        if "email" in objective_text:
            steps.append(
                ExecutionStep(
                    step_id=f"step-{len(steps) + 1}",
                    agent_type="tool",
                    action="send_email",
                    input_payload={
                        "objective": request.objective,
                        "context": request.context,
                    },
                )
            )

        if "notify" in objective_text:
            steps.append(
                ExecutionStep(
                    step_id=f"step-{len(steps) + 1}",
                    agent_type="tool",
                    action="notify_user",
                    input_payload={
                        "objective": request.objective,
                        "context": request.context,
                    },
                )
            )

        if not steps:
            steps.append(
                ExecutionStep(
                    step_id="step-1",
                    agent_type="generalist",
                    action="analyze_request",
                    input_payload={
                        "objective": request.objective,
                        "context": request.context,
                    },
                )
            )

        return ExecutionPlan(
            plan_id=f"plan-{request.request_id}",
            request_id=request.request_id,
            steps=steps,
        )
