from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.celery_app import celery_app


@pytest.fixture(autouse=True, scope="module")
def eager_celery():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    celery_app.conf.broker_url = "memory://"
    celery_app.conf.result_backend = "cache+memory://"
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False


def test_health():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_analyze_pr_validation_error():
    client = TestClient(app)
    resp = client.post("/analyze-pr", json={"repo_url": "not-a-url", "pr_number": 1})
    assert resp.status_code in (400, 422)


@patch("app.services.github.fetch_pr_data")
@patch("app.agent.reviewer.analyze_pr_with_agent")
@patch("app.services.cache.get_redis")
def test_analyze_pr_flow(mock_redis, mock_agent, mock_fetch):
    class FakeRedis:
        def __init__(self):
            self.store = {}
        def get(self, k):
            return self.store.get(k)
        def setex(self, k, ttl, v):
            self.store[k]=v
    mock_redis.return_value = FakeRedis()
    mock_fetch.return_value = type("PR", (), {
        "owner": "user", "repo": "repo", "number": 1, "title": "t", "body": "b",
        "head_sha": "abc", "base_sha": "def", "files": [], "diff": ""
    })
    mock_agent.return_value = type("Res", (), {
        "model_dump": lambda self=None: {"repo_url": "https://github.com/user/repo", "pr_number": 1, "head_sha": "abc", "summary": "ok", "issues": [], "model_info": {}}
    })()

    client = TestClient(app)
    resp = client.post("/analyze-pr", json={"repo_url": "https://github.com/user/repo", "pr_number": 1})
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]

    status = client.get(f"/status/{task_id}")
    assert status.status_code == 200

    results = client.get(f"/results/{task_id}")
    assert results.status_code == 200
    data = results.json()
    assert data["pr_number"] == 1
