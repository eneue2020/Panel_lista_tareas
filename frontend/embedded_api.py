"""Arranca la API de FastAPI dentro del mismo proceso que Streamlit.

Así basta con un solo despliegue (por ejemplo en Streamlit Community Cloud):
la API corre en un hilo en segundo plano y el panel le habla por HTTP como siempre.
"""

import socket
import sys
import threading
import time
from pathlib import Path

import uvicorn

PROJECT_DIR = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_api(timeout: float = 15) -> str:
    """Levanta la API en un puerto libre y devuelve su URL base cuando ya acepta peticiones."""
    # streamlit run solo agrega frontend/ al path; el paquete app/ está en la raíz del proyecto
    if str(PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIR))
    from app.main import app

    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, name="embedded-api", daemon=True)
    thread.start()

    deadline = time.monotonic() + timeout
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            raise RuntimeError("No se pudo arrancar la API integrada")
        time.sleep(0.05)
    return f"http://127.0.0.1:{port}"
