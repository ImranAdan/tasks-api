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
| `GET /tasks` | List tasks by ID, or only finished or open ones with `done=true` or `done=false`. `title=milk` keeps only tasks whose title contains "milk", ignoring case | 200 |
| `GET /tasks/{id}` | Read a task | 200 |
| `PUT /tasks/{id}` | Replace a task's `title` and `done` | 200 |
| `DELETE /tasks/{id}` | Delete a task | 204 |

An unknown ID returns 404. An empty or missing `title`, or a `done` filter other than `true` or `false`, returns 422.

## How pull requests are decided

After CI, `.github/workflows/mandate.yml` runs [Mandate](https://github.com/ImranAdan/mandate) on the PR and posts the result as the `mandate/decision` check. It builds the PR's app and runs it in a container with no secrets, no access to the runner's files and no internet. It then runs hidden acceptance tests against it, so link the issue you're working on, for example with `Closes #2`.

If the settings name a model, it also asks that model to score the change, and it shows the model's response on the check. A `claude-*` model runs on Anthropic's API; any other runs on the same machine.

It records decisions and merges nothing while `dry_run` is on. With `dry_run` off, it merges the exact commit it authorized.

The [design](https://github.com/ImranAdan/mandate/blob/main/docs/design.md) shows the whole flow, with diagrams.
