import pytest
from fastapi.testclient import TestClient

import tasks_api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKS_DB", str(tmp_path / "tasks.db"))
    return TestClient(tasks_api.app)


def test_create_then_read(client):
    created = client.post("/tasks", json={"title": "Buy milk"})
    assert created.status_code == 201
    assert created.json() == {"id": 1, "title": "Buy milk", "done": False}

    read = client.get("/tasks/1")
    assert read.status_code == 200
    assert read.json() == {"id": 1, "title": "Buy milk", "done": False}


def test_list_returns_every_task_in_order(client):
    client.post("/tasks", json={"title": "First"})
    client.post("/tasks", json={"title": "Second", "done": True})

    listed = client.get("/tasks")
    assert listed.status_code == 200
    assert listed.json() == [
        {"id": 1, "title": "First", "done": False},
        {"id": 2, "title": "Second", "done": True},
    ]


def test_update_changes_the_stored_task(client):
    client.post("/tasks", json={"title": "Buy milk"})

    updated = client.put("/tasks/1", json={"title": "Buy oat milk", "done": True})
    assert updated.status_code == 200
    assert updated.json() == {"id": 1, "title": "Buy oat milk", "done": True}
    assert client.get("/tasks/1").json() == {"id": 1, "title": "Buy oat milk", "done": True}


def test_update_leaves_other_tasks_alone(client):
    client.post("/tasks", json={"title": "First"})
    client.post("/tasks", json={"title": "Second"})

    client.put("/tasks/1", json={"title": "Changed", "done": True})
    assert client.get("/tasks/2").json() == {"id": 2, "title": "Second", "done": False}


def test_delete_removes_only_that_task(client):
    client.post("/tasks", json={"title": "First"})
    client.post("/tasks", json={"title": "Second"})

    deleted = client.delete("/tasks/1")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get("/tasks/1").status_code == 404
    assert client.get("/tasks").json() == [{"id": 2, "title": "Second", "done": False}]


@pytest.mark.parametrize(
    "method, kwargs",
    [
        ("get", {}),
        ("put", {"json": {"title": "Anything"}}),
        ("delete", {}),
    ],
)
def test_unknown_task_is_404(client, method, kwargs):
    response = getattr(client, method)("/tasks/99", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": "task not found"}


@pytest.mark.parametrize("body", [{"title": ""}, {}])
def test_a_task_needs_a_title(client, body):
    assert client.post("/tasks", json=body).status_code == 422
    assert client.get("/tasks").json() == []
