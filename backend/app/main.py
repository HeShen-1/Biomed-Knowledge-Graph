from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.errors import AppError, app_error_handler

app = FastAPI(title="Biomed Knowledge Graph API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)

from app.routers import graph, search, ingest
app.include_router(graph.router)
app.include_router(search.router)
app.include_router(ingest.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
