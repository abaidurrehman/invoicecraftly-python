# Changelog

## 0.1.1 — 2026-09-08

- Refresh the public README and package metadata so the PyPI project page no longer carries pre-release wording.
- Keep the SDK/API behavior unchanged from `0.1.0`.
- Synchronize the reported SDK version with the published package version.

## 0.1.0 — 2026-09-08

- Publish the first synchronous Python client for the released InvoiceCraftly API `v1` surface.
- Add typed request/response shapes for PDF, readiness and structured EN16931-core output.
- Preserve public API status/code/request-ID/details/Retry-After metadata in `InvoiceCraftlyError`.
- Add explicit timeout and network error mapping.
- Add `PdfResult.write_to(...)` as an opt-in file convenience.
- Keep zero runtime dependencies and ship `py.typed`.
- Publish through PyPI Trusted Publishing/OIDC.
- Verify a clean public-registry install and import of `invoicecraftly==0.1.0`.
