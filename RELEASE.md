# Releasing `invoicecraftly`

This is the release handoff for the official InvoiceCraftly Python client.

## Current state

- PyPI project: `invoicecraftly`
- current published version: `0.1.0`
- public repository: `abaidurrehman/invoicecraftly-python`
- Python: 3.11+
- runtime dependencies: none
- license: MIT
- API target: InvoiceCraftly API `v1`
- PyPI Trusted Publishing/OIDC: verified through the `pypi` GitHub environment
- clean public-registry install/import: verified for `invoicecraftly==0.1.0`

The first release was published on 8 September 2026 through `.github/workflows/release.yml` using PyPI Trusted Publishing/OIDC. No long-lived PyPI token is required in the repository.

## Release checks

From the package root:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src
python -m pip install --upgrade build
python -m build
```

Inspect both artifacts before publication. The wheel/sdist must contain no API keys, `.env` files, monorepo governance files, or unrelated private material.

Test the built wheel locally in a clean virtual environment before publishing a new version.

## PyPI Trusted Publishing

The release workflow is:

```text
.github/workflows/release.yml
```

Trusted Publisher identity:

```text
PyPI project:      invoicecraftly
GitHub owner:      abaidurrehman
Repository:        invoicecraftly-python
Workflow filename: release.yml
Environment:       pypi
```

Normal releases are tag-driven. Update the package version and changelog, validate the package, then push the reviewed release tag. Do not add a long-lived PyPI API token merely to automate releases.

## 0.1.0 verification evidence

The first release has independently verified:

1. the public repository resolves;
2. `invoicecraftly` `0.1.0` is published on PyPI;
3. a clean GitHub-hosted environment installed `invoicecraftly==0.1.0` from `https://pypi.org/simple` with no repository checkout;
4. import succeeds and reports SDK version `0.1.0`;
5. wheel/sdist contents were inspected;
6. PyPI JSON metadata reports the expected Homepage, Documentation, Source and Issues URLs;
7. those published project URLs resolve successfully.

The remaining Feature 102.10C product-level acceptance gate is the README PDF fixture against the real InvoiceCraftly API with an authorized test key. `/developers/` should expose the Python install/source path only after that gate is deliberately closed.
