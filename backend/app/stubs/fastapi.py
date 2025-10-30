"""Fallback stand-ins for the parts of FastAPI used in tests.

The execution environment that powers the kata does not allow installing
third-party packages.  To keep the public API compatible with the FastAPI-based
implementation while avoiding import errors, we provide lightweight no-op
replacements that mimic the signatures relied upon by :mod:`app.main`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class UploadFile:
    filename: str
    file: Any


class JSONResponse(dict):
    def __init__(self, content: Any, status_code: int = 200):
        super().__init__(content)
        self.status_code = status_code


class CORSMiddleware:  # pragma: no cover - behaviour-less placeholder
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        pass


class FastAPI:
    def __init__(self, title: str | None = None):
        self.title = title

    def add_middleware(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        pass

    def post(self, _path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator


def File(default: Any) -> Any:  # pragma: no cover - used for signature parity
    return default


def Form(default: Any) -> Any:  # pragma: no cover - used for signature parity
    return default


__all__ = [
    "FastAPI",
    "UploadFile",
    "File",
    "Form",
    "HTTPException",
    "JSONResponse",
    "CORSMiddleware",
]
