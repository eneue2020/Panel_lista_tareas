"""Punto de entrada: crea la aplicación FastAPI y conecta sus piezas."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="API de tareas", version="1.0.0", lifespan=lifespan)
app.include_router(router)
