# invoicecraftly

Official Python client for the [InvoiceCraftly Developer Document API](https://invoicecraftly.com/developers/).

Use it to generate an invoice PDF, check EN16931-core readiness, or prepare the currently supported EN16931-core XML artifact. The package is intentionally a thin HTTP client: InvoiceCraftly's API remains authoritative for invoice validation, calculations, readiness and rendering.

## Status

Engineering-ready beta client for InvoiceCraftly API `v1`. Planned first release: `0.1.0`.

**PyPI publication has not happened yet.** The package name `invoicecraftly` is the preferred candidate and must be rechecked directly on PyPI immediately before reservation/publication. The install command below becomes a public release claim only after a clean registry install succeeds.

## Install after publication

```bash
pip install invoicecraftly
```

## Requirements

- Python 3.11 or newer
- an InvoiceCraftly Developer API key
- server-side code or another trusted environment where the API key can remain secret

Do **not** put an InvoiceCraftly API key in browser JavaScript, commit it to Git, or include it in public logs.

## Generate a PDF

```python
import os

from invoicecraftly import InvoiceCraftly

client = InvoiceCraftly(api_key=os.environ["INVOICECRAFTLY_API_KEY"])

invoice = {
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

result = client.documents.pdf(invoice)
result.write_to("invoice.pdf")
print(result.render_duration_ms, result.request_id)
```

The fictional fixture intentionally matches InvoiceCraftly's canonical developer example.

## Check EN16931-core readiness

```python
supplement = {
    "version": 1,
    "seller": {
        "postalAddress": {
            "countryCode": "NO",
            "city": "Oslo",
            "postalCode": "0154",
        },
        "taxId": {"role": "legal-registration", "schemeId": "0192"},
        "vatIdentifier": "NO123456785MVA",
    },
    "lines": [{"sourceIndex": 0, "unitCode": "HUR", "vatCategoryCode": "S"}],
}

readiness = client.invoices.readiness({"document": invoice, "supplement": supplement})

if not readiness["ready"]:
    print(readiness["gaps"])
```

This is the currently released **EN16931-core** readiness surface. It is not a Peppol BIS conformance or delivery claim.

## Generate the currently supported structured XML

```python
structured = client.documents.structured({"document": invoice, "supplement": supplement})

if structured["ready"] and structured["artifact"]:
    print(structured["artifact"]["content"])
```

`prepared` is not `sent`: this client does not submit invoices to Peppol or another delivery network.

## Error handling

```python
from invoicecraftly import InvoiceCraftlyError

try:
    result = client.documents.pdf(invoice)
except InvoiceCraftlyError as error:
    print(error.status, error.code, error.request_id)
    if error.retry_after_seconds is not None:
        print(f"Retry after {error.retry_after_seconds:g}s")
```

Public API failures preserve HTTP status, public error code, request ID, details and `Retry-After` where available. Local transport failures use `NETWORK_ERROR`, `REQUEST_TIMEOUT`, or `UNEXPECTED_RESPONSE`.

## Timeout policy

The default request timeout is 20 seconds. Override it on the client or one request:

```python
client = InvoiceCraftly(
    api_key=os.environ["INVOICECRAFTLY_API_KEY"],
    timeout=15,
)

result = client.documents.pdf(invoice, timeout=30)
```

The first release is synchronous and intentionally does not hide retries or background work.

## Privacy and security

Calling the Developer Document API is remote processing initiated by your integration. The SDK itself has no telemetry and makes no tracking calls. It does not persist invoice bodies or PDFs; `PdfResult.write_to(...)` writes bytes only when your code explicitly asks it to.

Never post real invoice/customer/payment data in a public GitHub issue. See:

- https://invoicecraftly.com/privacy/
- https://invoicecraftly.com/security/

## API compatibility

Package version and API version are separate. `invoicecraftly` `0.x` targets the released InvoiceCraftly API `v1` surface documented at https://invoicecraftly.com/developers/.

The client intentionally does not implement invoice totals, VAT rules, route decisions, EN16931 validation rules, Peppol logic, or delivery logic locally.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q src
python -m build
```

The package has zero runtime dependencies and ships a `py.typed` marker for type-checker discovery.

## Release preparation

See [`RELEASE.md`](./RELEASE.md). The first public release should use a dedicated `release.yml` workflow and PyPI Trusted Publishing/OIDC rather than a long-lived PyPI token.

## Support

Use this repository's Issues tab for SDK bugs or documentation problems that contain no sensitive invoice data. For account-specific or sensitive matters, use InvoiceCraftly's contact/security routes instead of a public issue.

## License

MIT
