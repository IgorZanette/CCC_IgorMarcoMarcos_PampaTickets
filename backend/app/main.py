from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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
    relatorios,
    webhooks,
)
from app.core.logging_config import setup_logging
from app.core.rate_limit import limiter
from app.db.session import init_db
from app.integrations.asaas.client import close_client as close_asaas_client
from app.integrations.whatsapp.client import close_client as close_whatsapp_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    setup_logging()
    await init_db()
    yield
    await close_asaas_client()
    await close_whatsapp_client()


app = FastAPI(
    title="PampaTickets API",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(relatorios.router, prefix="/api")


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


FAVICON_PATH = Path(__file__).parent / "static" / "favicon.svg"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(FAVICON_PATH, media_type="image/svg+xml")


@app.get("/", tags=["Health Check"])
def read_root() -> dict[str, str]:
    return {"status": "ok", "service": "PampaTickets Core API"}
