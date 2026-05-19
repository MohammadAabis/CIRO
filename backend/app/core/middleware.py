"""
HTTP error-handling middleware for consistent API responses.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

logger = logging.getLogger("ciro.http")
logger.setLevel(logging.INFO)


def add_error_handling_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except RequestValidationError as exc:
            logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
            return JSONResponse(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                content={"error": "validation_error", "detail": exc.errors()},
            )
        except HTTPException as exc:
            logger.info("HTTP error on %s %s: %s", request.method, request.url.path, exc.detail)
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail, "status_code": exc.status_code},
            )
        except Exception as exc:
            logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "internal_server_error", "detail": "Unhandled server error"},
            )
