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


@pytest.mark.parametrize(
    "query, expected",
    [
        ("?done=false", [{"id": 1, "title": "Open", "done": False}]),
        ("?done=true", [{"id": 2, "title": "Finished", "done": True}]),
        (
            "",
            [
                {"id": 1, "title": "Open", "done": False},
                {"id": 2, "title": "Finished", "done": True},
            ],
        ),
    ],
)
def test_list_filters_by_done(client, query, expected):
    client.post("/tasks", json={"title": "Open"})
    client.post("/tasks", json={"title": "Finished", "done": True})

    listed = client.get(f"/tasks{query}")
    assert listed.status_code == 200
    assert listed.json() == expected


def test_done_filter_with_no_matches_is_an_empty_list(client):
    client.post("/tasks", json={"title": "Open"})

    listed = client.get("/tasks?done=true")
    assert listed.status_code == 200
    assert listed.json() == []


@pytest.mark.parametrize("value", ["maybe", "", "1", "0", "yes", "TRUE", "true' OR '1'='1"])
def test_invalid_done_filter_is_422(client, value):
    client.post("/tasks", json={"title": "Open"})

    assert client.get("/tasks", params={"done": value}).status_code == 422
    assert client.get("/tasks").json() == [{"id": 1, "title": "Open", "done": False}]


def test_sql_in_a_title_is_stored_as_plain_text(client):
    created = "x'); DROP TABLE task; --"
    client.post("/tasks", json={"title": "Other"})
    assert client.post("/tasks", json={"title": created}).json()["title"] == created
    assert client.get("/tasks/2").json()["title"] == created

    updated = "y' WHERE 1=1; DELETE FROM task; --"
    assert client.put("/tasks/2", json={"title": updated, "done": True}).json()["title"] == updated
    assert client.get("/tasks").json() == [
        {"id": 1, "title": "Other", "done": False},
        {"id": 2, "title": updated, "done": True},
    ]
