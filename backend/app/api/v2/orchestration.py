from typing import Any, Dict

from fastapi import APIRouter, Depends
from celery.result import AsyncResult

from ...core.api_key_dependency import require_platform_api_key
from ...core.celery import celery_app
from ...orchestration.schemas import ExecutionRequest
from ...tasks.orchestration_task import run_orchestration

router = APIRouter()


@router.post("/execute")
async def execute(
    request: ExecutionRequest,
    api_key: Dict[str, Any] = Depends(require_platform_api_key),
) -> Dict[str, str]:
    _ = api_key
    task = run_orchestration.delay(request.model_dump())
    return {"execution_id": task.id}


@router.get("/execute/{execution_id}")
async def get_execution_status(
    execution_id: str,
    api_key: Dict[str, Any] = Depends(require_platform_api_key),
) -> Dict[str, object]:
    _ = api_key
    task = AsyncResult(execution_id, app=celery_app)
    return {
        "execution_id": execution_id,
        "status": task.status,
        "result": task.result if task.successful() else None,
    }
