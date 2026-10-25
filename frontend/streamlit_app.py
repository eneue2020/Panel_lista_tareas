"""Panel visual de tareas hecho con Streamlit. Consume la API REST de FastAPI."""

import os
import re
from datetime import datetime

import httpx
import streamlit as st

from api_client import ApiError, TodoApi

API_URL = os.environ.get("TODOS_API_URL", "http://localhost:8000")

STATUS_BADGE = {
    "pending": ":orange-badge[Pendiente]",
    "done": ":green-badge[Completada]",
}

FILTERS = {"Todas": None, "Pendientes": "pending", "Completadas": "done"}

# Proporciones de las columnas de la tabla: tarea, descripción, estado, acciones
COLUMNS = [2.8, 2.6, 1.4, 1.6]


@st.cache_resource
def get_api() -> TodoApi:
    return TodoApi(httpx.Client(base_url=API_URL, timeout=5))


def md_escape(text: str) -> str:
    """Escapa caracteres de Markdown para que el texto del usuario se muestre tal cual."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|~<>$:])", r"\\\1", text)


def format_date(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone().strftime("%d/%m/%Y %H:%M")


def flash(kind: str, message: str) -> None:
    """Guarda un mensaje para mostrarlo después del st.rerun()."""
    st.session_state["flash"] = (kind, message)


def run_action(action, success_message: str) -> None:
    try:
        action()
        flash("success", success_message)
    except ApiError as exc:
        flash("error", str(exc))
    st.rerun()


# ---------- Página ----------

st.set_page_config(page_title="Panel de tareas", page_icon="✅", layout="wide")
st.title("✅ Panel de tareas")

api = get_api()

if "flash" in st.session_state:
    kind, message = st.session_state.pop("flash")
    getattr(st, kind)(message)

try:
    todos = api.list_todos()
except ApiError as exc:
    st.error(f"{exc}. ¿Está corriendo el backend en {API_URL}?")
    st.code("uvicorn app.main:app --reload --port 8000", language="bash")
    st.stop()

# ---------- Resumen ----------

total = len(todos)
done = sum(1 for t in todos if t["status"] == "done")
pending = total - done

col_total, col_pending, col_done = st.columns(3)
col_total.metric("Total", total, border=True)
col_pending.metric("Pendientes", pending, border=True)
col_done.metric("Completadas", done, border=True)

# ---------- Formulario de creación ----------

with st.form("new_todo", clear_on_submit=True):
    st.subheader("Nueva tarea")
    title = st.text_input("Título *", max_chars=200, placeholder="¿Qué hay que hacer?")
    description = st.text_area("Descripción", max_chars=2000, placeholder="Opcional")
    submitted = st.form_submit_button("Crear tarea", type="primary")

if submitted:
    if not title.strip():
        st.warning("El título es obligatorio.")
    else:
        run_action(
            lambda: api.create_todo(title, description.strip() or None),
            f"Tarea «{md_escape(title.strip())}» creada.",
        )

# ---------- Tabla de tareas ----------

st.subheader("Tareas")
selected = st.segmented_control("Mostrar", list(FILTERS), default="Todas", label_visibility="collapsed")
status_filter = FILTERS.get(selected)
visible = [t for t in todos if status_filter is None or t["status"] == status_filter]

if not visible:
    st.info("No hay tareas para mostrar." if todos else "Todavía no hay tareas. ¡Creá la primera!")
else:
    header = st.columns(COLUMNS, vertical_alignment="center")
    for col, label in zip(header, ["Tarea", "Descripción", "Estado", "Acciones"]):
        col.markdown(f"**{label}**")

    for todo in visible:
        is_done = todo["status"] == "done"
        title_md = md_escape(todo["title"])

        with st.container(border=True):
            row = st.columns(COLUMNS, vertical_alignment="center")
            # Las completadas se ven tachadas y en gris
            row[0].markdown(
                (f":gray[~~{title_md}~~]" if is_done else f"**{title_md}**")
                + f"  \n:gray[\\#{todo['id']} · {format_date(todo['created_at'])}]"
            )
            row[1].markdown(md_escape(todo["description"]) if todo["description"] else ":gray[—]")
            row[2].markdown(STATUS_BADGE[todo["status"]])

            if not is_done and row[3].button(
                "Completar", key=f"complete-{todo['id']}", icon=":material/check:", type="primary", width="stretch"
            ):
                run_action(lambda: api.complete_todo(todo["id"]), f"Tarea «{title_md}» completada.")
            if row[3].button("Eliminar", key=f"delete-{todo['id']}", icon=":material/delete:", width="stretch"):
                run_action(lambda: api.delete_todo(todo["id"]), f"Tarea «{title_md}» eliminada.")
