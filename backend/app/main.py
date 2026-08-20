import logging
# pyrefly: ignore [missing-import]
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI         
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.db.iniciar_bd import iniciar_base_datos
from app.api.routes.encuestas import router as router_encuestas
from app.api.routes.tablero import router as router_tablero
from app.api.routes.ia import router as router_ia
from app.api.routes.reportes import router as router_reportes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("encuestas_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        iniciar_base_datos()
        logger.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
    yield


app = FastAPI(
    title="Plataforma de Análisis de Encuestas - Campus Córdoba",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_encuestas, prefix="/api")
app.include_router(router_tablero, prefix="/api")
app.include_router(router_ia, prefix="/api")
app.include_router(router_reportes, prefix="/api")


@app.get("/health")
def health_check():
    """Endpoint simple para confirmar que el backend está corriendo."""
    return {"status": "ok"}
