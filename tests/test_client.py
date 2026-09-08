from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError

from invoicecraftly import InvoiceCraftly, InvoiceCraftlyError
from invoicecraftly.client import _TransportResponse

FIXTURE = {
    "type": "invoice",
    "number": "INV-1042",
    "issueDate": "2026-09-05",
    "dueDate": "2026-09-19",
    "currency": "USD",
    "seller": {
        "name": "Fixture Seller Studio",
        "addressLines": ["12 Render Way", "Austin, TX 73301", "United States"],
    },
    "buyer": {
        "name": "Fixture Buyer Co",
        "addressLines": ["400 Client Ave", "Denver, CO 80202", "United States"],
    },
    "items": [
        {
            "description": "Brand design retainer",
            "quantity": 2,
            "unitPrice": 150,
            "taxRate": 8.25,
            "taxLabel": "Sales Tax",
        }
    ],
    "payment": {
        "iban": "DE89370400440532013000",
        "reference": "INV-1042",
        "terms": "Net 14",
    },
}


class ClientTests(unittest.TestCase):
    def test_documents_pdf_sends_exact_public_v1_semantics_and_returns_bytes(self) -> None:
        seen: dict[str, object] = {}

        def transport(url, body, headers, timeout):
            seen.update(url=url, body=body, headers=headers, timeout=timeout)
            return _TransportResponse(
                200,
                {"content-type": "application/pdf", "x-render-duration-ms": "321", "x-request-id": "req_pdf"},
                b"%PDF",
            )

        client = InvoiceCraftly(api_key="dk_live_test", transport=transport)
        result = client.documents.pdf(FIXTURE)
        self.assertEqual(seen["url"], "https://invoicecraftly.com/api/v1/documents/pdf")
        self.assertEqual(seen["headers"]["Authorization"], "Bearer dk_live_test")
        self.assertEqual(seen["headers"]["Content-Type"], "application/json")
        self.assertEqual(seen["headers"]["Accept"], "application/pdf")
        self.assertEqual(json.loads(seen["body"].decode("utf-8")), FIXTURE)
        self.assertEqual(result.data, b"%PDF")
        self.assertEqual(result.render_duration_ms, 321.0)
        self.assertEqual(result.request_id, "req_pdf")

    def test_pdf_write_to_is_a_file_convenience_only(self) -> None:
        client = InvoiceCraftly(
            api_key="dk_live_test",
            transport=lambda *_: _TransportResponse(200, {"content-type": "application/pdf"}, b"%PDF"),
        )
        result = client.documents.pdf(FIXTURE)
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "invoice.pdf"
            self.assertEqual(result.write_to(target), target)
            self.assertEqual(target.read_bytes(), b"%PDF")

    def test_readiness_targets_released_endpoint(self) -> None:
        seen = {}

        def transport(url, *_):
            seen["url"] = url
            body = json.dumps({
                "apiVersion": "v1",
                "profileId": "en16931-core",
                "specificationIdentifier": "urn:test",
                "ready": False,
                "gaps": [{"id": "X", "message": "Missing field"}],
            }).encode()
            return _TransportResponse(200, {"content-type": "application/json"}, body)

        result = InvoiceCraftly(api_key="dk_live_test", transport=transport).invoices.readiness({"document": FIXTURE})
        self.assertEqual(seen["url"], "https://invoicecraftly.com/api/v1/invoices/readiness")
        self.assertFalse(result["ready"])
        self.assertEqual(result["gaps"][0]["id"], "X")

    def test_structured_targets_released_endpoint(self) -> None:
        seen = {}

        def transport(url, *_):
            seen["url"] = url
            body = json.dumps({
                "apiVersion": "v1",
                "profileId": "en16931-core",
                "specificationIdentifier": "urn:test",
                "ready": True,
                "gaps": [],
                "artifact": {"mediaType": "application/xml", "content": "<Invoice />"},
            }).encode()
            return _TransportResponse(200, {"content-type": "application/json"}, body)

        result = InvoiceCraftly(api_key="dk_live_test", transport=transport).documents.structured({"document": FIXTURE})
        self.assertEqual(seen["url"], "https://invoicecraftly.com/api/v1/documents/structured")
        self.assertEqual(result["artifact"]["content"], "<Invoice />")

    def test_public_api_errors_preserve_stable_metadata(self) -> None:
        body = json.dumps({
            "error": {
                "code": "RATE_LIMITED",
                "message": "Slow down.",
                "requestId": "req_123",
                "details": [{"field": "items"}],
            }
        }).encode()
        client = InvoiceCraftly(
            api_key="dk_live_test",
            transport=lambda *_: _TransportResponse(429, {"retry-after": "7"}, body),
        )
        with self.assertRaises(InvoiceCraftlyError) as caught:
            client.documents.pdf(FIXTURE)
        error = caught.exception
        self.assertEqual(error.status, 429)
        self.assertEqual(error.code, "RATE_LIMITED")
        self.assertEqual(error.request_id, "req_123")
        self.assertEqual(error.retry_after_seconds, 7.0)
        self.assertEqual(error.details, [{"field": "items"}])

    def test_authentication_failures_remain_distinguishable(self) -> None:
        body = json.dumps({"error": {"code": "AUTHENTICATION_FAILED", "message": "Bad key", "details": []}}).encode()
        client = InvoiceCraftly(api_key="bad", transport=lambda *_: _TransportResponse(401, {}, body))
        with self.assertRaises(InvoiceCraftlyError) as caught:
            client.documents.pdf(FIXTURE)
        self.assertEqual(caught.exception.status, 401)
        self.assertEqual(caught.exception.code, "AUTHENTICATION_FAILED")

    def test_malformed_5xx_fails_closed_without_inventing_details(self) -> None:
        client = InvoiceCraftly(api_key="dk_live_test", transport=lambda *_: _TransportResponse(503, {}, b"bad gateway"))
        with self.assertRaises(InvoiceCraftlyError) as caught:
            client.documents.pdf(FIXTURE)
        self.assertEqual(caught.exception.status, 503)
        self.assertEqual(caught.exception.code, "HTTP_ERROR")
        self.assertIsNone(caught.exception.request_id)

    def test_timeout_maps_to_request_timeout_without_leaking_key(self) -> None:
        def transport(*_):
            raise TimeoutError("socket timed out")

        client = InvoiceCraftly(api_key="dk_live_super_secret", timeout=0.01, transport=transport)
        with self.assertRaises(InvoiceCraftlyError) as caught:
            client.documents.pdf(FIXTURE)
        self.assertEqual(caught.exception.code, "REQUEST_TIMEOUT")
        self.assertNotIn("dk_live_super_secret", str(caught.exception))

    def test_urlerror_timeout_maps_to_request_timeout(self) -> None:
        def transport(*_):
            raise URLError(TimeoutError("timed out"))

        client = InvoiceCraftly(api_key="dk_live_test", transport=transport)
        with self.assertRaises(InvoiceCraftlyError) as caught:
            client.documents.pdf(FIXTURE)
        self.assertEqual(caught.exception.code, "REQUEST_TIMEOUT")

    def test_network_failure_maps_to_network_error_without_leaking_key(self) -> None:
        def transport(*_):
            raise OSError("network down")

        client = InvoiceCraftly(api_key="dk_live_super_secret", transport=transport)
        with self.assertRaises(InvoiceCraftlyError) as caught:
            client.documents.pdf(FIXTURE)
        self.assertEqual(caught.exception.code, "NETWORK_ERROR")
        self.assertNotIn("dk_live_super_secret", str(caught.exception))

    def test_unexpected_pdf_content_type_fails_closed(self) -> None:
        client = InvoiceCraftly(
            api_key="dk_live_test",
            transport=lambda *_: _TransportResponse(200, {"content-type": "application/json", "x-request-id": "req_bad"}, b"{}"),
        )
        with self.assertRaises(InvoiceCraftlyError) as caught:
            client.documents.pdf(FIXTURE)
        self.assertEqual(caught.exception.code, "UNEXPECTED_RESPONSE")
        self.assertEqual(caught.exception.request_id, "req_bad")

    def test_constructor_rejects_empty_credentials_and_bad_base_url(self) -> None:
        with self.assertRaises(TypeError):
            InvoiceCraftly(api_key="")
        with self.assertRaises(TypeError):
            InvoiceCraftly(api_key="dk_live_test", base_url="javascript:alert(1)")
        with self.assertRaises(TypeError):
            InvoiceCraftly(api_key="dk_live_test", base_url="https://invoicecraftly.com?x=1")


if __name__ == "__main__":
    unittest.main()
