from __future__ import annotations

import asyncio
from typing import Any, Dict, List
import structlog

from .agent_dispatcher import AgentDispatcher
from .planner import Planner
from .runtime_limits import MAX_AGENT_STEPS, MAX_RUNTIME_SECONDS
from .schemas import ExecutionRequest, ExecutionResult, ExecutionStep

logger = structlog.get_logger()


class SupervisorAgent:
    def __init__(self) -> None:
        self.planner = Planner()
        self.dispatcher = AgentDispatcher()

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        plan = await self.planner.create_plan(request)

        step_cap = min(request.max_steps or MAX_AGENT_STEPS, MAX_AGENT_STEPS)
        steps = plan.steps[:step_cap]
        step_results: List[Dict[str, Any]] = []
        execution_log: List[Dict[str, str]] = []
        context: Dict[str, Any] = {}

        async def run_single_step(step: ExecutionStep, context_snapshot: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(
                "Execution step started",
                step_id=step.step_id,
                action=step.action,
            )
            runtime_payload = {
                **step.input_payload,
                "context": dict(context_snapshot),
            }
            return await self.dispatcher.dispatch_step(
                ExecutionStep(
                    step_id=step.step_id,
                    agent_type=step.agent_type,
                    action=step.action,
                    input_payload=runtime_payload,
                )
            )

        try:
            async with asyncio.timeout(MAX_RUNTIME_SECONDS):
                idx = 0
                while idx < len(steps):
                    step = steps[idx]
                    parallel_group = step.input_payload.get("parallel_group")

                    if parallel_group:
                        group_steps: List[ExecutionStep] = []
                        while idx < len(steps) and steps[idx].input_payload.get("parallel_group") == parallel_group:
                            group_steps.append(steps[idx])
                            idx += 1

                        context_snapshot = dict(context)
                        results = await asyncio.gather(
                            *[run_single_step(group_step, context_snapshot) for group_step in group_steps]
                        )

                        for group_step, result in zip(group_steps, results):
                            status = "success" if "error" not in result else "failed"
                            execution_log.append(
                                {
                                    "step_id": group_step.step_id,
                                    "action": group_step.action,
                                    "status": status,
                                }
                            )
                            logger.info(
                                "Execution step completed",
                                step_id=group_step.step_id,
                                action=group_step.action,
                                status=status,
                                result=result,
                            )
                            step_results.append(result)
                            context[group_step.step_id] = result
                    else:
                        result = await run_single_step(step, context)
                        status = "success" if "error" not in result else "failed"
                        execution_log.append(
                            {
                                "step_id": step.step_id,
                                "action": step.action,
                                "status": status,
                            }
                        )
                        logger.info(
                            "Execution step completed",
                            step_id=step.step_id,
                            action=step.action,
                            status=status,
                            result=result,
                        )
                        step_results.append(result)
                        context[step.step_id] = result
                        idx += 1

            logger.info("Execution completed", execution_log=execution_log)
            return ExecutionResult(
                request_id=request.request_id,
                plan_id=plan.plan_id,
                status="success",
                step_results=step_results,
            )
        except Exception as exc:
            logger.error("Execution failed", error=str(exc), execution_log=execution_log)
            return ExecutionResult(
                request_id=request.request_id,
                plan_id=plan.plan_id,
                status="failed",
                step_results=step_results,
                error=str(exc),
            )
