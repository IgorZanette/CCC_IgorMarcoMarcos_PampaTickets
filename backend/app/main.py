from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.middleware.logging import LoggingMiddleware
from app.api.routes import (
    auth,
    checkin,
    cortesias,
    cupons,
    eventos,
    ingressos,
    lotes,
    pedidos,
    webhooks,
)
from app.core.logging_config import setup_logging
from app.db.session import init_db
from app.integrations.asaas.client import close_client as close_asaas_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    setup_logging()
    await init_db()
    yield
    await close_asaas_client()


app = FastAPI(
    title="PampaTickets API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(auth.router, prefix="/api")
app.include_router(eventos.router, prefix="/api")
app.include_router(lotes.router, prefix="/api")
app.include_router(pedidos.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(checkin.router, prefix="/api")
app.include_router(ingressos.router, prefix="/api")
app.include_router(cupons.router, prefix="/api")
app.include_router(cortesias.router, prefix="/api")


@app.exception_handler(Exception)
async def excecao_nao_tratada(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "Exceção não tratada | {} {} | request_id={}",
        request.method,
        request.url.path,
        request_id,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor.",
            "request_id": request_id,
        },
    )


@app.get("/", tags=["Health Check"])
def read_root() -> dict[str, str]:
    return {"status": "ok", "service": "PampaTickets Core API"}
