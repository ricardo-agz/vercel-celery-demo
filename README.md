# Celery task demo

This demo publishes Celery tasks through Vercel Queues and reads their results
through Celery's `AsyncResult` API. `vercel-celery` configures `vercel://` as
the broker and `vercel-runtime-cache://` as the default result backend. Results
expire from Vercel Runtime Cache after one hour.

The `[[tool.vercel.subscribers]]` declaration points to `worker:app`. During
the build, Vercel imports that module, discovers the queues registered by the
Celery app, and generates the queue triggers and subscriber function. No
hand-written queue trigger or worker endpoint is needed.

## Run it

Use Vercel CLI 58.4.0 or newer. Older CLIs use the legacy Python subscriber
schema and require manually listed topics instead of build-time introspection.

Link the directory to a Vercel project, then start Vercel's development server:

```sh
uv sync
vc link
vc dev
```

`vc dev` does not emulate Runtime Cache, so the demo uses a shared temporary
filesystem result backend only when `VERCEL_ENV=development`. Preview and
production use the default `vercel-runtime-cache://` backend.

## Enqueue and inspect a task

```sh
curl -i -X POST http://127.0.0.1:3000/tasks/add \
  -H 'content-type: application/json' \
  -d '{"x": 20, "y": 22}'
```

The response contains a `task_id` and a `Location` header. Use that ID to
retrieve the current state and eventual result:

```sh
curl http://127.0.0.1:3000/tasks/TASK_ID
```

Valid operations are `add`, `multiply`, and `subtract`. Interactive API
documentation is available at <http://127.0.0.1:3000/docs>.

Deploy with `vc deploy`.
# vercel-celery-demo
