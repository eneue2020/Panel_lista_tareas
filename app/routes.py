"""Rutas HTTP de la API de tareas."""

import sqlite3
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app import database
from app.models import Status, Todo, TodoCreate, TodoUpdate

router = APIRouter(prefix="/api/todos", tags=["todos"])

Db = Annotated[sqlite3.Connection, Depends(database.get_db)]
TodoId = Annotated[int, Path(gt=0, description="ID de la tarea")]


def not_found(todo_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No existe ninguna tarea con id {todo_id}",
    )


@router.get("", response_model=list[Todo])
def list_todos(
    db: Db,
    status_filter: Annotated[
        Optional[Status], Query(alias="status", description="Filtra por estado: pending o done")
    ] = None,
):
    return database.list_todos(db, status_filter)


@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: TodoId, db: Db):
    todo = database.get_todo(db, todo_id)
    if todo is None:
        raise not_found(todo_id)
    return todo


@router.post("", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(data: TodoCreate, db: Db):
    return database.create_todo(db, data.title, data.description)


@router.patch("/{todo_id}", response_model=Todo)
def update_todo(todo_id: TodoId, data: TodoUpdate, db: Db):
    # Solo los campos que vinieron en el cuerpo de la petición
    changes = data.model_dump(exclude_unset=True)
    todo = database.update_todo(db, todo_id, changes)
    if todo is None:
        raise not_found(todo_id)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: TodoId, db: Db):
    if not database.delete_todo(db, todo_id):
        raise not_found(todo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
