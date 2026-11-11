import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

SCHEMA = (Path(__file__).parent / "schema.sql").read_text()

app = FastAPI(title="tasks-api")


class TaskIn(BaseModel):
    title: str = Field(min_length=1)
    done: bool = False


class Task(TaskIn):
    id: int


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(os.environ.get("TASKS_DB", "tasks.db"))
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        with conn:
            yield conn
    finally:
        conn.close()


def found(conn: sqlite3.Connection, task_id: int) -> Task:
    row = conn.execute("SELECT id, title, done FROM task WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "task not found")
    return Task(**dict(row))


@app.post("/tasks", status_code=201)
def create_task(task: TaskIn) -> Task:
    with database() as conn:
        created = conn.execute("INSERT INTO task (title, done) VALUES (?, ?)", (task.title, task.done))
        return found(conn, created.lastrowid)


@app.get("/tasks")
def list_tasks(done: Literal["true", "false"] | None = None, title: str | None = None) -> list[Task]:
    """Every task, or only those matching the filters. A title search ignores case and has no wildcards."""
    where, params = [], []
    if done is not None:
        where.append("done = ?")
        params.append(done == "true")
    if title is not None:
        where.append("instr(lower(title), lower(?)) > 0")
        params.append(title)
    query = "SELECT id, title, done FROM task" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY id"
    with database() as conn:
        return [Task(**dict(row)) for row in conn.execute(query, params).fetchall()]


@app.get("/tasks/{task_id}")
def read_task(task_id: int) -> Task:
    with database() as conn:
        return found(conn, task_id)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskIn) -> Task:
    with database() as conn:
        conn.execute("UPDATE task SET title = ?, done = ? WHERE id = ?", (task.title, task.done, task_id))
        return found(conn, task_id)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> Response:
    with database() as conn:
        if conn.execute("DELETE FROM task WHERE id = ?", (task_id,)).rowcount == 0:
            raise HTTPException(404, "task not found")
    return Response(status_code=204)


@app.delete("/tasks", status_code=204)
def clear_tasks() -> Response:
    """Delete every task, to start a fresh list."""
    with database() as conn:
        conn.execute("DELETE FROM task")
    return Response(status_code=204)
