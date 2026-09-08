from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, cast
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from .errors import InvoiceCraftlyError
from .types import PublicDocumentV1, PublicStructuredRequestV1, ReadinessResultV1, StructuredResultV1

INVOICECRAFTLY_API_VERSION = "v1"
INVOICECRAFTLY_SDK_VERSION = "0.1.1"
DEFAULT_BASE_URL = "https://invoicecraftly.com"
DEFAULT_TIMEOUT_SECONDS = 20.0


@dataclass(frozen=True)
class PdfResult:
    data: bytes
    render_duration_ms: float | None = None
    request_id: str | None = None

    def write_to(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_bytes(self.data)
        return destination


@dataclass(frozen=True)
class _TransportResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


Transport = Callable[[str, bytes, Mapping[str, str], float], _TransportResponse]


def _normalize_base_url(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError("InvoiceCraftly base_url must be a non-empty absolute http(s) URL.")
    parsed = urllib_parse.urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise TypeError("InvoiceCraftly base_url must be an absolute http(s) URL.")
    if parsed.query or parsed.fragment:
        raise TypeError("InvoiceCraftly base_url must not contain a query string or fragment.")
    return value.strip().rstrip("/")


def _normalize_timeout(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise TypeError("InvoiceCraftly timeout must be a positive number of seconds.")
    return float(value)


def _headers_lower(headers: Mapping[str, str]) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items()}


def _header(headers: Mapping[str, str], name: str) -> str | None:
    return _headers_lower(headers).get(name.lower())


def _header_number(headers: Mapping[str, str], name: str) -> float | None:
    raw = _header(headers, name)
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _default_transport(url: str, body: bytes, headers: Mapping[str, str], timeout: float) -> _TransportResponse:
    request = urllib_request.Request(url, data=body, headers=dict(headers), method="POST")
    try:
        with urllib_request.urlopen(request, timeout=timeout) as response:
            return _TransportResponse(
                status=int(response.status),
                headers={key.lower(): value for key, value in response.headers.items()},
                body=response.read(),
            )
    except urllib_error.HTTPError as exc:
        return _TransportResponse(
            status=int(exc.code),
            headers={key.lower(): value for key, value in exc.headers.items()},
            body=exc.read(),
        )


def _request_id(response: _TransportResponse, payload: Mapping[str, Any] | None = None) -> str | None:
    error_value = payload.get("error") if payload else None
    if isinstance(error_value, Mapping):
        body_value = error_value.get("requestId")
        if isinstance(body_value, str) and body_value:
            return body_value
    return _header(response.headers, "x-request-id")


def _parse_api_error(response: _TransportResponse) -> InvoiceCraftlyError:
    payload: Mapping[str, Any] | None = None
    try:
        decoded = json.loads(response.body.decode("utf-8"))
        if isinstance(decoded, Mapping):
            payload = decoded
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = None

    error_value = payload.get("error") if payload else None
    error_payload = error_value if isinstance(error_value, Mapping) else {}
    raw_code = error_payload.get("code")
    raw_message = error_payload.get("message")
    raw_details = error_payload.get("details")

    code = raw_code if isinstance(raw_code, str) and raw_code else "HTTP_ERROR"
    message = (
        raw_message
        if isinstance(raw_message, str) and raw_message
        else f"InvoiceCraftly API request failed with HTTP {response.status}."
    )
    details = raw_details if isinstance(raw_details, list) else []
    return InvoiceCraftlyError(
        message,
        status=response.status,
        code=code,
        request_id=_request_id(response, payload),
        details=details,
        retry_after_seconds=_header_number(response.headers, "retry-after"),
    )


def _decode_json_object(response: _TransportResponse) -> dict[str, Any]:
    try:
        payload = json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvoiceCraftlyError(
            "InvoiceCraftly returned invalid JSON.",
            status=response.status,
            code="UNEXPECTED_RESPONSE",
            request_id=_request_id(response),
            cause=exc,
        ) from exc
    if not isinstance(payload, dict):
        raise InvoiceCraftlyError(
            "InvoiceCraftly returned an unexpected JSON response shape.",
            status=response.status,
            code="UNEXPECTED_RESPONSE",
            request_id=_request_id(response),
        )
    return payload


class _Documents:
    def __init__(self, client: "InvoiceCraftly") -> None:
        self._client = client

    def pdf(self, document: PublicDocumentV1, *, timeout: float | None = None) -> PdfResult:
        return self._client._pdf(document, timeout=timeout)

    def structured(
        self,
        request: PublicStructuredRequestV1,
        *,
        timeout: float | None = None,
    ) -> StructuredResultV1:
        return self._client._structured(request, timeout=timeout)


class _Invoices:
    def __init__(self, client: "InvoiceCraftly") -> None:
        self._client = client

    def readiness(
        self,
        request: PublicStructuredRequestV1,
        *,
        timeout: float | None = None,
    ) -> ReadinessResultV1:
        return self._client._readiness(request, timeout=timeout)


class InvoiceCraftly:
    """Synchronous thin client for the released InvoiceCraftly API v1 surface."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        transport: Transport | None = None,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise TypeError("InvoiceCraftly api_key must be a non-empty string.")
        self._api_key = api_key.strip()
        self._base_url = _normalize_base_url(base_url)
        self._timeout = _normalize_timeout(timeout)
        self._transport = transport or _default_transport
        self.documents = _Documents(self)
        self.invoices = _Invoices(self)

    def _post(
        self,
        path: str,
        body: object,
        *,
        accept: str,
        timeout: float | None,
    ) -> _TransportResponse:
        request_timeout = _normalize_timeout(timeout if timeout is not None else self._timeout)
        try:
            encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise TypeError("InvoiceCraftly request body must be JSON serializable.") from exc

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": accept,
            "User-Agent": f"invoicecraftly-python/{INVOICECRAFTLY_SDK_VERSION}",
        }
        try:
            response = self._transport(f"{self._base_url}{path}", encoded, headers, request_timeout)
        except InvoiceCraftlyError:
            raise
        except (TimeoutError, socket.timeout) as exc:
            raise InvoiceCraftlyError(
                f"InvoiceCraftly request timed out after {request_timeout:g} seconds.",
                code="REQUEST_TIMEOUT",
                cause=exc,
            ) from exc
        except urllib_error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise InvoiceCraftlyError(
                    f"InvoiceCraftly request timed out after {request_timeout:g} seconds.",
                    code="REQUEST_TIMEOUT",
                    cause=exc,
                ) from exc
            raise InvoiceCraftlyError(
                "InvoiceCraftly request failed before a response was received.",
                code="NETWORK_ERROR",
                cause=exc,
            ) from exc
        except OSError as exc:
            raise InvoiceCraftlyError(
                "InvoiceCraftly request failed before a response was received.",
                code="NETWORK_ERROR",
                cause=exc,
            ) from exc

        if response.status < 200 or response.status >= 300:
            raise _parse_api_error(response)
        return response

    def _pdf(self, document: PublicDocumentV1, *, timeout: float | None) -> PdfResult:
        response = self._post(
            "/api/v1/documents/pdf",
            document,
            accept="application/pdf",
            timeout=timeout,
        )
        content_type = (_header(response.headers, "content-type") or "").lower()
        if not content_type.startswith("application/pdf"):
            raise InvoiceCraftlyError(
                "InvoiceCraftly returned an unexpected response type for PDF generation.",
                status=response.status,
                code="UNEXPECTED_RESPONSE",
                request_id=_request_id(response),
            )
        return PdfResult(
            data=response.body,
            render_duration_ms=_header_number(response.headers, "x-render-duration-ms"),
            request_id=_request_id(response),
        )

    def _readiness(
        self,
        request: PublicStructuredRequestV1,
        *,
        timeout: float | None,
    ) -> ReadinessResultV1:
        response = self._post(
            "/api/v1/invoices/readiness",
            request,
            accept="application/json",
            timeout=timeout,
        )
        return cast(ReadinessResultV1, _decode_json_object(response))

    def _structured(
        self,
        request: PublicStructuredRequestV1,
        *,
        timeout: float | None,
    ) -> StructuredResultV1:
        response = self._post(
            "/api/v1/documents/structured",
            request,
            accept="application/json",
            timeout=timeout,
        )
        return cast(StructuredResultV1, _decode_json_object(response))
