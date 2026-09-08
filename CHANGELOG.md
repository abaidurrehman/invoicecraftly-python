# Changelog

## 0.1.0 — prepared, not yet published

- Add the first synchronous Python client for the released InvoiceCraftly API `v1` surface.
- Add typed request/response shapes for PDF, readiness and structured EN16931-core output.
- Preserve public API status/code/request-ID/details/Retry-After metadata in `InvoiceCraftlyError`.
- Add explicit timeout and network error mapping.
- Add `PdfResult.write_to(...)` as an opt-in file convenience.
- Keep zero runtime dependencies and ship `py.typed`.

Publication date will be recorded only after the package is actually released and verified from PyPI.
