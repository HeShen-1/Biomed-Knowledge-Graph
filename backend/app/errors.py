from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    def __init__(self, message: str = ""):
        self.message = message


class GraphTimeoutError(AppError):
    status_code = 408
    code = "GRAPH_TIMEOUT"


class EntityNotFoundError(AppError):
    status_code = 404
    code = "ENTITY_NOT_FOUND"


class InvalidParamError(AppError):
    status_code = 400
    code = "INVALID_PARAM"


class UpstreamError(AppError):
    status_code = 502
    code = "UPSTREAM_ERROR"


class IngestInProgressError(AppError):
    status_code = 503
    code = "INGEST_IN_PROGRESS"


async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "request_id": getattr(request.state, "request_id", ""),
        },
    )
