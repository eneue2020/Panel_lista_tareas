"""Test de la API integrada que arranca el panel cuando no hay TODOS_API_URL."""

import httpx

from app import database
from frontend.embedded_api import start_api


def test_embedded_api_serves_requests(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "embedded.db")

    base_url = start_api()

    with httpx.Client(base_url=base_url) as client:
        assert client.get("/api/todos").json() == []
        created = client.post("/api/todos", json={"title": "Desde la API integrada"})
        assert created.status_code == 201
        assert client.get("/api/todos").json() == [created.json()]
