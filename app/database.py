"""Acceso a la base de datos SQLite con el módulo estándar sqlite3 (sin ORM)."""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

PROJECT_DIR = Path(__file__).resolve().parent.parent

# Se puede cambiar con la variable de entorno TODOS_DB (los tests usan una base temporal).
DB_PATH = Path(os.environ.get("TODOS_DB", PROJECT_DIR / "todos.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT,
    status      TEXT    NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'done')),
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
)
"""

# Columnas que se pueden modificar con un UPDATE. Lista cerrada: nunca viene del usuario.
UPDATABLE_COLUMNS = {"title", "description", "status"}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """Dependencia de FastAPI: abre una conexión por petición y la cierra al terminar."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Operaciones sobre la tabla todos ----------

def list_todos(conn: sqlite3.Connection, status: Optional[str] = None) -> list[dict]:
    if status:
        rows = conn.execute(
            "SELECT * FROM todos WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM todos ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def get_todo(conn: sqlite3.Connection, todo_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return dict(row) if row else None


def create_todo(conn: sqlite3.Connection, title: str, description: Optional[str]) -> dict:
    timestamp = _now()
    with conn:
        cur = conn.execute(
            "INSERT INTO todos (title, description, status, created_at, updated_at) "
            "VALUES (?, ?, 'pending', ?, ?)",
            (title, description, timestamp, timestamp),
        )
    return get_todo(conn, cur.lastrowid)


def update_todo(conn: sqlite3.Connection, todo_id: int, changes: dict) -> Optional[dict]:
    """Actualiza solo las columnas de `changes`. Devuelve None si la tarea no existe."""
    unknown = set(changes) - UPDATABLE_COLUMNS
    if unknown:
        raise ValueError(f"Columnas no actualizables: {unknown}")

    fields = {**changes, "updated_at": _now()}
    assignments = ", ".join(f"{column} = ?" for column in fields)
    with conn:
        cur = conn.execute(
            f"UPDATE todos SET {assignments} WHERE id = ?",
            (*fields.values(), todo_id),
        )
    if cur.rowcount == 0:
        return None
    return get_todo(conn, todo_id)


def delete_todo(conn: sqlite3.Connection, todo_id: int) -> bool:
    """Devuelve True si se borró la tarea, False si no existía."""
    with conn:
        cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    return cur.rowcount > 0
