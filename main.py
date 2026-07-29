from typing import Literal

from celery import states
from celery.result import AsyncResult
from fastapi import FastAPI, Response, status
from pydantic import BaseModel

from worker import add, app as celery_app, multiply, subtract


app = FastAPI(title="Celery task demo")


class TaskInput(BaseModel):
    x: int
    y: int


class EnqueuedTask(BaseModel):
    task_id: str
    status: str


class TaskResult(BaseModel):
    task_id: str
    status: str
    result: int | None = None
    error: str | None = None


tasks = {
    "add": add,
    "multiply": multiply,
    "subtract": subtract,
}


@app.get("/")
def read_root():
    return {
        "message": "Submit a task with POST /tasks/{operation}",
        "operations": list(tasks),
    }


@app.post(
    "/tasks/{operation}",
    response_model=EnqueuedTask,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_task(
    operation: Literal["add", "multiply", "subtract"],
    payload: TaskInput,
    response: Response,
) -> EnqueuedTask:
    task = tasks[operation].delay(payload.x, payload.y)
    response.headers["Location"] = f"/tasks/{task.id}"
    return EnqueuedTask(task_id=task.id, status=states.PENDING)


@app.get("/tasks/{task_id}", response_model=TaskResult)
def get_task_result(task_id: str) -> TaskResult:
    task = AsyncResult(task_id, app=celery_app)
    task_state = task.state

    if task_state == states.FAILURE:
        return TaskResult(
            task_id=task_id,
            status=task_state,
            error=str(task.result),
        )
    if task_state == states.SUCCESS:
        return TaskResult(
            task_id=task_id,
            status=task_state,
            result=task.result,
        )

    return TaskResult(task_id=task_id, status=task_state)
