"""
orders/errors.py

Identical structured-error envelope to catalog/errors.py (Listing 3.16).
Centralising the rendering here prevents any endpoint from leaking an
unstructured error, even in the presence of bugs or framework defaults.
"""
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class APIError(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        type: str,                                    # noqa: A002
        message: str,
        field: Optional[str] = None,
        hint: Optional[str] = None,
        retryable: bool = False,
        retry_after_ms: Optional[int] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.payload = {
            "error_code": error_code,
            "type": type,
            "message": message,
            "field": field,
            "hint": hint,
            "retryable": retryable,
            "retry_after_ms": retry_after_ms,
        }


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def handle_api_error(_: Request, exc: APIError):
        return JSONResponse(status_code=exc.status_code, content=exc.payload)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError):
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = first.get("loc", [])
        field = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else None
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_FAILED",
                "type": "validation_error",
                "message": first.get("msg", "Validation failed."),
                "field": field,
                "hint": None,
                "retryable": False,
                "retry_after_ms": None,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "type": "server_error",
                "message": "An unexpected error occurred.",
                "field": None,
                "hint": None,
                "retryable": True,
                "retry_after_ms": 5000,
            },
        )
