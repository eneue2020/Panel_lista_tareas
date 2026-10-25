"""Cliente HTTP de la API de tareas. El panel no habla con la base de datos: solo con la API."""

from typing import Optional

import httpx


class ApiError(Exception):
    """Error devuelto por la API, con un mensaje listo para mostrar al usuario."""


def _error_message(response: httpx.Response) -> str:
    # 404 → {"detail": "texto"}   422 → {"detail": [{"loc": [...], "msg": "..."}, ...]}
    try:
        detail = response.json().get("detail")
    except ValueError:
        return f"Error {response.status_code} de la API"
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        parts = []
        for error in detail:
            field = ".".join(str(p) for p in error.get("loc", []) if p != "body")
            parts.append(f"{field}: {error.get('msg')}" if field else error.get("msg", ""))
        return ". ".join(parts)
    return f"Error {response.status_code} de la API"


class TodoApi:
    def __init__(self, client: httpx.Client):
        # Se recibe el cliente desde fuera: en la app es un httpx.Client real
        # y en los tests es el TestClient de FastAPI.
        self.client = client

    def _request(self, method: str, url: str, **kwargs) -> Optional[dict | list]:
        try:
            response = self.client.request(method, url, **kwargs)
        except httpx.TransportError as exc:
            raise ApiError(f"No se pudo conectar con la API ({exc.__class__.__name__})") from exc
        if response.is_error:
            raise ApiError(_error_message(response))
        if response.status_code == 204:
            return None
        return response.json()

    def list_todos(self, status: Optional[str] = None) -> list[dict]:
        params = {"status": status} if status else None
        return self._request("GET", "/api/todos", params=params)

    def create_todo(self, title: str, description: Optional[str] = None) -> dict:
        return self._request("POST", "/api/todos", json={"title": title, "description": description})

    def complete_todo(self, todo_id: int) -> dict:
        return self._request("PATCH", f"/api/todos/{todo_id}", json={"status": "done"})

    def delete_todo(self, todo_id: int) -> None:
        self._request("DELETE", f"/api/todos/{todo_id}")
