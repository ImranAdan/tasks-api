# tasks-api

A small CRUD API that an agent builds and Mandate merges. It has one resource, `task`, stored in SQLite, with no UI, login or deployment.

## Run it

```bash
uv sync
uv run uvicorn tasks_api:app
```

The database file is `tasks.db`, or whatever `TASKS_DB` names. Interactive docs are at `http://127.0.0.1:8000/docs`.

## Test it

```bash
uv run pytest
```

## API

| Method and path | Does | Success |
|---|---|---|
| `POST /tasks` | Create a task from `title` and optional `done` | 201 |
| `GET /tasks` | List tasks by ID | 200 |
| `GET /tasks/{id}` | Read a task | 200 |
| `PUT /tasks/{id}` | Replace a task's `title` and `done` | 200 |
| `DELETE /tasks/{id}` | Delete a task | 204 |

An unknown ID returns 404, and an empty or missing `title` returns 422.
