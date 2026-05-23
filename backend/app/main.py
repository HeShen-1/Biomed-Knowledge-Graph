from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uuid import uuid4
from app.errors import AppError, app_error_handler
from app.config import validate_config_on_startup

app = FastAPI(title="Biomed Knowledge Graph API", version="0.1.0")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)


@app.exception_handler(Exception)
async def catch_all_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred", "request_id": getattr(request.state, "request_id", "")},
    )


@app.on_event("startup")
async def startup():
    import logging
    validate_config_on_startup()
    import asyncio
    from app.db.neo4j import verify_indexes
    task = asyncio.create_task(verify_indexes())
    task.add_done_callback(
        lambda t: logging.getLogger(__name__).error(
            "verify_indexes failed: %s", t.exception()
        ) if t.exception() else None
    )


from app.routers import graph, search, ingest
app.include_router(graph.router)
app.include_router(search.router)
app.include_router(ingest.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
