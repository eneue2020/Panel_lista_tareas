import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Cliente de pruebas con una base de datos nueva y vacía en cada test."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    # El bloque `with` ejecuta el lifespan de la app, que crea la tabla.
    with TestClient(app) as c:
        yield c


@pytest.fixture
def create_todo(client):
    """Atajo para crear tareas dentro de un test."""
    def _create(title="Tarea de prueba", description=None):
        response = client.post("/api/todos", json={"title": title, "description": description})
        assert response.status_code == 201
        return response.json()
    return _create
