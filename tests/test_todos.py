import pytest


# ---------- GET /api/todos ----------

def test_list_empty(client):
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_all(client, create_todo):
    create_todo("Primera")
    create_todo("Segunda")
    titles = [t["title"] for t in client.get("/api/todos").json()]
    assert titles == ["Primera", "Segunda"]


def test_list_filters_by_status(client, create_todo):
    done = create_todo("Hecha")
    create_todo("Pendiente")
    client.patch(f"/api/todos/{done['id']}", json={"status": "done"})

    pending = client.get("/api/todos", params={"status": "pending"}).json()
    finished = client.get("/api/todos", params={"status": "done"}).json()

    assert [t["title"] for t in pending] == ["Pendiente"]
    assert [t["title"] for t in finished] == ["Hecha"]


def test_list_rejects_unknown_status(client):
    response = client.get("/api/todos", params={"status": "finished"})
    assert response.status_code == 422


# ---------- GET /api/todos/{id} ----------

def test_get_todo(client, create_todo):
    todo = create_todo("Leer", "Capítulo 3")
    response = client.get(f"/api/todos/{todo['id']}")
    assert response.status_code == 200
    assert response.json() == todo


def test_get_missing_todo_returns_404(client):
    response = client.get("/api/todos/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "No existe ninguna tarea con id 999"}


@pytest.mark.parametrize("bad_id", ["abc", "0", "-1"])
def test_get_invalid_id_returns_422(client, bad_id):
    assert client.get(f"/api/todos/{bad_id}").status_code == 422


# ---------- POST /api/todos ----------

def test_create_todo(client):
    response = client.post("/api/todos", json={"title": "Estudiar FastAPI", "description": "Rutas"})
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "Estudiar FastAPI"
    assert body["description"] == "Rutas"
    assert body["status"] == "pending"
    assert body["created_at"] == body["updated_at"]


def test_create_without_description(client):
    response = client.post("/api/todos", json={"title": "Solo título"})
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_strips_whitespace(client):
    response = client.post("/api/todos", json={"title": "  Comprar pan  "})
    assert response.json()["title"] == "Comprar pan"


@pytest.mark.parametrize(
    "payload",
    [
        {},                                     # falta el título
        {"title": ""},                          # vacío
        {"title": "    "},                      # solo espacios
        {"title": None},                        # null
        {"title": 123},                         # no es texto
        {"title": "x" * 201},                   # demasiado largo
        {"title": "Ok", "description": 5},      # descripción que no es texto
        {"title": "Ok", "status": "done"},      # campo no permitido al crear
        {"title": "Ok", "id": 7},               # campo desconocido
    ],
)
def test_create_rejects_invalid_data(client, payload):
    response = client.post("/api/todos", json=payload)
    assert response.status_code == 422
    assert client.get("/api/todos").json() == []


def test_create_rejects_malformed_json(client):
    response = client.post(
        "/api/todos", content="{no es json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


# ---------- PATCH /api/todos/{id} ----------

def test_update_status(client, create_todo):
    todo = create_todo("Lavar ropa")
    response = client.patch(f"/api/todos/{todo['id']}", json={"status": "done"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["title"] == "Lavar ropa"  # lo que no se envía no cambia
    assert body["updated_at"] > todo["updated_at"]


def test_update_title_and_description(client, create_todo):
    todo = create_todo("Viejo", "Desc vieja")
    response = client.patch(
        f"/api/todos/{todo['id']}", json={"title": "Nuevo", "description": "Desc nueva"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Nuevo"
    assert response.json()["description"] == "Desc nueva"


def test_update_can_clear_description(client, create_todo):
    todo = create_todo("Con descripción", "Algo")
    response = client.patch(f"/api/todos/{todo['id']}", json={"description": None})
    assert response.json()["description"] is None


def test_update_is_persisted(client, create_todo):
    todo = create_todo()
    client.patch(f"/api/todos/{todo['id']}", json={"status": "done"})
    assert client.get(f"/api/todos/{todo['id']}").json()["status"] == "done"


def test_update_missing_todo_returns_404(client):
    response = client.patch("/api/todos/999", json={"status": "done"})
    assert response.status_code == 404
    assert response.json() == {"detail": "No existe ninguna tarea con id 999"}


@pytest.mark.parametrize(
    "payload",
    [
        {},                         # nada que actualizar
        {"status": "finished"},     # estado desconocido
        {"status": None},           # estado null
        {"title": None},            # título null
        {"title": "   "},           # título vacío
        {"completed": True},        # campo desconocido
    ],
)
def test_update_rejects_invalid_data(client, create_todo, payload):
    todo = create_todo("Original")
    response = client.patch(f"/api/todos/{todo['id']}", json=payload)
    assert response.status_code == 422
    assert client.get(f"/api/todos/{todo['id']}").json() == todo


# ---------- DELETE /api/todos/{id} ----------

def test_delete_todo(client, create_todo):
    todo = create_todo()
    response = client.delete(f"/api/todos/{todo['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/todos/{todo['id']}").status_code == 404


def test_delete_only_removes_that_todo(client, create_todo):
    keep = create_todo("Se queda")
    remove = create_todo("Se va")
    client.delete(f"/api/todos/{remove['id']}")
    assert client.get("/api/todos").json() == [keep]


def test_delete_missing_todo_returns_404(client):
    response = client.delete("/api/todos/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "No existe ninguna tarea con id 999"}
