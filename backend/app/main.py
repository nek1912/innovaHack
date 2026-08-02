import logging
import time
import uuid
from contextlib import asynccontextmanager

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import async_session
from app.routers import agent_payouts, owner_admin, audit, webhooks, credit
from app.services.reconciliation import reconcile_stale_payouts

logger = logging.getLogger("app.access")

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        reconcile_stale_payouts,
        "interval",
        minutes=10,
        id="reconcile_stale_payouts",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Agent Finance Control System", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal", "message": "An unexpected error occurred"},
    )


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra={"request_id": request_id, "method": request.method, "path": request.url.path},
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-Id"] = request_id
    logger.info(
        "%s %s -> %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        extra={"request_id": request_id},
    )
    return response


app.include_router(agent_payouts.router)
app.include_router(owner_admin.router)
app.include_router(audit.router)
app.include_router(webhooks.router)
app.include_router(credit.router)


@app.get("/health")
async def health():
    checks = {}
    # DB check
    try:
        async with async_session() as db:
            await db.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "down"
    # OPA check
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.opa_url}/health")
            checks["opa"] = "ok" if resp.status_code == 200 else "degraded"
    except Exception:
        checks["opa"] = "down"

    healthy = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "healthy" if healthy else "degraded", "checks": checks},
    )
