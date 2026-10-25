# Lista de tareas: API REST + panel visual

- **Backend:** API REST con **FastAPI** y **SQLite** (módulo estándar `sqlite3`, sin ORM), validación con **Pydantic**.
- **Frontend:** panel visual con **Streamlit** que consume la API por HTTP.
- **Tests:** **pytest** + `TestClient` de FastAPI (httpx).

## Cómo ejecutarla

Instalación (una sola vez):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Opción A: todo junto (un solo comando)

```bash
streamlit run frontend/streamlit_app.py
```

El panel arranca la API de FastAPI en un hilo en segundo plano, dentro del mismo proceso. Es el modo que se usa en Streamlit Cloud.

- Panel: http://localhost:8501 (o el puerto que indique Streamlit)

### Opción B: API y panel por separado

Útil para desarrollar la API o usar su documentación interactiva. Hacen falta dos terminales con el entorno virtual activado:

```bash
# Terminal 1: la API
uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2: el panel, apuntando a esa API (PowerShell)
$env:TODOS_API_URL = "http://localhost:8000"
streamlit run frontend/streamlit_app.py
```

- API: http://localhost:8000/api/todos
- Documentación interactiva de la API (Swagger): http://localhost:8000/docs

**Regla:** si existe la variable `TODOS_API_URL`, el panel usa esa API; si no, arranca la suya propia.

## Despliegue en Streamlit Community Cloud

1. Entrá en https://share.streamlit.io con tu cuenta de GitHub.
2. **Create app** → desplegar desde un repositorio de GitHub.
3. Repository: `eneue2020/Panel_lista_tareas` · Branch: `main` · Main file path: `frontend/streamlit_app.py`.
4. En **Advanced settings**, elegí Python 3.11.
5. **Deploy**.

No hace falta configurar nada más: la API se arranca dentro de la app.

> **Ojo:** en Streamlit Cloud el disco no es permanente. Las tareas guardadas en SQLite se pierden cuando la app se reinicia o se vuelve a desplegar.

## Tests

```bash
pytest
```

Cada test usa una base de datos temporal nueva, así que nunca tocan `todos.db`.

## Estructura

```
proyecto_2/
├── app/                   # Backend
│   ├── main.py            # Crea la app FastAPI y registra las rutas
│   ├── routes.py          # Endpoints HTTP; convierte "no existe" en HTTPException 404
│   ├── models.py          # Modelos Pydantic: validan la entrada y describen la salida
│   └── database.py        # Conexión SQLite, creación de la tabla y consultas SQL
├── frontend/              # Panel visual
│   ├── streamlit_app.py   # Interfaz: resumen, formulario y tabla de tareas
│   ├── api_client.py      # Cliente HTTP de la API (el panel no toca la base de datos)
│   └── embedded_api.py    # Arranca la API en segundo plano si no hay TODOS_API_URL
├── tests/
│   ├── conftest.py        # Fixtures: cliente de pruebas con base de datos temporal
│   ├── test_todos.py      # Tests de los cinco endpoints de la API
│   ├── test_api_client.py # Tests del cliente que usa el panel, contra la API real
│   └── test_embedded_api.py # Test de la API integrada
├── requirements.txt
└── pytest.ini
```

Cada capa tiene una sola responsabilidad: `database.py` no sabe nada de HTTP, `routes.py` no escribe SQL, `models.py` no depende de ninguna de las dos, y el panel solo habla con la API.

## Panel visual

- **Resumen:** total de tareas, pendientes y completadas.
- **Formulario** para crear tareas con título (obligatorio) y descripción (opcional).
- **Tabla de tareas** con el estado en color: naranja para *Pendiente* y verde para *Completada*. Las completadas además se ven tachadas.
- **Botón Completar** en cada tarea pendiente y **botón Eliminar** en todas.
- Filtro para ver todas, solo pendientes o solo completadas.
- Si la API no responde, el panel lo avisa en lugar de fallar.

## API

| Método | Ruta | Qué hace | Respuesta |
|---|---|---|---|
| GET | `/api/todos` | Lista las tareas. Filtro opcional: `?status=pending` o `?status=done` | 200 / 422 |
| GET | `/api/todos/{id}` | Devuelve el detalle de una tarea | 200 / 404 / 422 |
| POST | `/api/todos` | Crea una tarea. Cuerpo: `title` (obligatorio), `description` (opcional) | 201 / 422 |
| PATCH | `/api/todos/{id}` | Actualiza `title`, `description` y/o `status`; solo cambia los campos enviados | 200 / 404 / 422 |
| DELETE | `/api/todos/{id}` | Elimina una tarea | 204 / 404 / 422 |

### Modelo de tarea

```json
{
  "id": 1,
  "title": "Estudiar FastAPI",
  "description": "Rutas y Pydantic",
  "status": "pending",
  "created_at": "2026-10-25T21:06:31.943629+00:00",
  "updated_at": "2026-10-25T21:06:31.943629+00:00"
}
```

### Reglas de validación

- `title`: texto obligatorio, de 1 a 200 caracteres. Se recortan los espacios de los extremos; un título solo de espacios se rechaza.
- `description`: texto opcional, de hasta 2000 caracteres. En PATCH, `null` borra la descripción.
- `status`: solo `pending` o `done`. Las tareas nuevas empiezan siempre en `pending`.
- Los tipos son estrictos: un número o un booleano no se aceptan como texto.
- Se rechazan los campos desconocidos (por ejemplo `id` o `completed`) y un PATCH sin campos.
- `id` en la URL debe ser un entero positivo.

### Errores

- **404**: la tarea no existe → `{"detail": "No existe ninguna tarea con id 999"}`
- **422**: datos de entrada inválidos. La respuesta indica qué campo falló y por qué.

### Ejemplos

```bash
curl -X POST http://localhost:8000/api/todos -H "Content-Type: application/json" -d '{"title": "Estudiar FastAPI"}'
curl "http://localhost:8000/api/todos?status=pending"
curl -X PATCH http://localhost:8000/api/todos/1 -H "Content-Type: application/json" -d '{"status": "done"}'
curl -X DELETE http://localhost:8000/api/todos/1
```
