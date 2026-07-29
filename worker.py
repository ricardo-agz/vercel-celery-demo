import os
import tempfile
from pathlib import Path

from celery import Celery
from vercel.integrations.celery import install_vercel_celery_integration

# Register Vercel Queues as the broker and Vercel Runtime Cache as Celery's
# default result backend. The Vercel Python builder uses the same integration
# to discover this app's queues from the subscriber declaration at build time.
install_vercel_celery_integration()

app = Celery("celery-task-demo")

app.conf.update(
    task_default_queue="celery",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    result_backend_transport_options={
        "namespace": "celery-task-demo-results",
        "ttl": 3600,
    },
    task_track_started=True,
)

# `vc dev` emulates Vercel Queues but not Runtime Cache. Its web and subscriber
# processes share the local filesystem, so use Celery's filesystem backend only
# in development. Preview and production keep the integration's default
# `vercel-runtime-cache://` backend configured above.
if os.getenv("VERCEL_ENV") == "development" or os.getenv("NOW_REGION") == "dev1":
    local_results = Path(tempfile.gettempdir()) / "celery-task-demo-results"
    local_results.mkdir(parents=True, exist_ok=True)
    app.conf.result_backend = f"file://{local_results}"


@app.task
def add(x: int, y: int) -> int:
    return x + y


@app.task
def multiply(x: int, y: int) -> int:
    return x * y


@app.task
def subtract(x: int, y: int) -> int:
    return x - y