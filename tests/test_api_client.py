"""Tests del cliente que usa el panel Streamlit, contra la API real (TestClient)."""

import httpx
import pytest

from frontend.api_client import ApiError, TodoApi


@pytest.fixture
def api(client):
    return TodoApi(client)


def test_create_and_list(api):
    created = api.create_todo("Desde el panel", "Con descripción")
    assert created["status"] == "pending"
    assert api.list_todos() == [created]


def test_list_with_status_filter(api):
    first = api.create_todo("Una")
    api.create_todo("Otra")
    api.complete_todo(first["id"])
    assert [t["title"] for t in api.list_todos("done")] == ["Una"]
    assert [t["title"] for t in api.list_todos("pending")] == ["Otra"]


def test_complete_todo(api):
    todo = api.create_todo("Completar")
    assert api.complete_todo(todo["id"])["status"] == "done"


def test_delete_todo(api):
    todo = api.create_todo("Borrar")
    assert api.delete_todo(todo["id"]) is None
    assert api.list_todos() == []


def test_not_found_raises_api_error(api):
    with pytest.raises(ApiError, match="No existe ninguna tarea con id 999"):
        api.delete_todo(999)


def test_validation_error_is_readable(api):
    with pytest.raises(ApiError, match="^title: "):
        api.create_todo("   ")


def test_connection_error_raises_api_error():
    api = TodoApi(httpx.Client(base_url="http://127.0.0.1:1", timeout=1))
    with pytest.raises(ApiError, match="No se pudo conectar"):
        api.list_todos()
