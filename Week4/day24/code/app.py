"""Day24 exercise: expose the completed batch service over HTTP."""

from dataclasses import asdict

from fastapi import Depends, FastAPI, HTTPException

from .api_models import BatchRequest
from .batch import Task, TaskReport, run_batch, validate_task_ids
from .retry_service import RetryResult
from .runtime import BatchRuntime, get_runtime
from .summary import summarize

app = FastAPI(title="Day24 offline batch API", debug=False)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "simulated"}


def make_response(rows: list[TaskReport]) -> dict:
    retry_result_list = []
    task_list = []
    for row in rows:
        retry_result = row.report
        retry_result_list.append(retry_result)
        task_list.append(asdict(row))
    summary = summarize(retry_result_list)
    result = {"mode": "simulated", "tasks": task_list, "summary": summary}
    return result


@app.post("/analyze-batch")
def analyze_batch(
        request: BatchRequest,
        runtime: BatchRuntime = Depends(get_runtime),
) -> dict:
    tasks = []
    for requested_task in request.tasks:
        task = Task(task_id=requested_task.task_id, text=requested_task.text)
        tasks.append(task)
    try:
        validate_task_ids(tasks)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"code": "DUPLICATE_TASK_ID", "message": "duplicate task_id"})
    rows=run_batch(tasks,runtime.gateway_factory,max_attempts=request.max_attempts,sleeper=runtime.sleeper)
    return make_response(rows)