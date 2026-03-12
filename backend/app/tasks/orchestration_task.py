import asyncio
from typing import Any, Dict

from ..core.celery import celery_app
from ..orchestration.schemas import ExecutionRequest
from ..orchestration.supervisor_agent import SupervisorAgent


@celery_app.task(name="app.tasks.orchestration_task.run_orchestration")
def run_orchestration(request_payload: Dict[str, Any]) -> Dict[str, Any]:
    request = ExecutionRequest(**request_payload)
    supervisor = SupervisorAgent()
    result = asyncio.run(supervisor.execute(request))
    return result.model_dump()
