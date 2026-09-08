# Releasing `invoicecraftly`

This is the release handoff for Feature 102.10C. Engineering may prepare the package, but PyPI claims stay false until independently verified.

## Current state

- preferred PyPI name: `invoicecraftly` — **provisional, not reserved or published**
- planned first version: `0.1.0`
- public repository: `abaidurrehman/invoicecraftly-python`
- Python: 3.11+
- runtime dependencies: none
- license: MIT
- API target: InvoiceCraftly API `v1`

A web-search preflight on 8 September 2026 found no exact PyPI result for `invoicecraftly`, `invoicecraftly-client`, or `invoicecraftly-sdk`; that is **not proof of registry availability**. Recheck the exact preferred name directly on PyPI immediately before creating the project/pending publisher.

## Pre-publication checks

From the package root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q src
python -m pip install --upgrade build
python -m build
```

Inspect both artifacts before publication. The wheel/sdist must contain no API keys, `.env` files, monorepo governance files, or unrelated private material.

Then test the wheel locally in a clean virtual environment before involving PyPI.

## PyPI Trusted Publishing

Prefer PyPI Trusted Publishing through GitHub Actions/OIDC. Do not create or store a long-lived PyPI API token merely to automate releases.

The prepared workflow is:

```text
.github/workflows/release.yml
```

Recommended PyPI Trusted Publisher fields:

```text
PyPI project:      invoicecraftly        (recheck exact name first)
GitHub owner:      abaidurrehman
Repository:        invoicecraftly-python
Workflow filename: release.yml
Environment:       pypi
```

PyPI supports a pending Trusted Publisher for a new project, but a pending publisher does **not** reserve the project name until it is actually used to publish. Configure it only after the repository/workflow identity is final.

## First release acceptance

Do not mark 102.10C complete until all are true:

1. the public repository resolves;
2. the exact PyPI project is actually published;
3. a clean virtual environment can `pip install <real-package-name>` from PyPI;
4. import succeeds and reports SDK version `0.1.0`;
5. built wheel/sdist contents are inspected;
6. the README PDF fixture succeeds against the real API with an authorized test key;
7. PyPI Homepage/Documentation/Source links resolve correctly;
8. `/developers/` is updated only after those external gates are true.
