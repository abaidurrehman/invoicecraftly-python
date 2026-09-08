from __future__ import annotations

from typing import Any, Iterable


class InvoiceCraftlyError(Exception):
    """Stable client exception for InvoiceCraftly API and transport failures."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        status: int | None = None,
        request_id: str | None = None,
        details: Iterable[Any] | None = None,
        retry_after_seconds: float | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.request_id = request_id
        self.details = list(details or [])
        self.retry_after_seconds = retry_after_seconds
        if cause is not None:
            self.__cause__ = cause
