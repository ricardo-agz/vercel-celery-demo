from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import main
from worker import app as celery_app


client = TestClient(main.app)


def test_celery_uses_vercel_queues_and_runtime_cache() -> None:
    assert celery_app.conf.broker_url == "vercel://"
    assert celery_app.conf.result_backend == "vercel-runtime-cache://"
    assert celery_app.conf.task_default_queue == "celery"
    assert celery_app.conf.result_backend_transport_options == {
        "namespace": "celery-task-demo-results",
        "ttl": 3600,
    }


def test_enqueue_task_returns_polling_location(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main.tasks["add"],
        "delay",
        lambda x, y: SimpleNamespace(id="task-123"),
    )

    response = client.post("/tasks/add", json={"x": 20, "y": 22})

    assert response.status_code == 202
    assert response.headers["location"] == "/tasks/task-123"
    assert response.json() == {"task_id": "task-123", "status": "PENDING"}


@pytest.mark.parametrize(
    ("state", "result", "expected"),
    [
        ("PENDING", None, {"task_id": "task-123", "status": "PENDING"}),
        (
            "SUCCESS",
            42,
            {"task_id": "task-123", "status": "SUCCESS", "result": 42},
        ),
        (
            "FAILURE",
            ValueError("bad input"),
            {"task_id": "task-123", "status": "FAILURE", "error": "bad input"},
        ),
    ],
)
def test_get_task_result(
    monkeypatch: pytest.MonkeyPatch,
    state: str,
    result: object,
    expected: dict[str, object],
) -> None:
    monkeypatch.setattr(
        main,
        "AsyncResult",
        lambda task_id, app: SimpleNamespace(state=state, result=result),
    )

    response = client.get("/tasks/task-123")

    assert response.status_code == 200
    assert response.json() == {
        **{"result": None, "error": None},
        **expected,
    }
