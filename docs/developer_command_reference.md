# Developer Command Reference

This reference defines short local task aliases for common workflows and maps
them to equivalent CI checks.

## Local task runner commands

Run from repository root:

| Workflow | Standard command | Short alias |
| --- | --- | --- |
| Unit tests | `make test` | `make t` |
| Governance docs/anchor checks | `make governance` | `make g` |
| Runtime stack checks | `make stack` | `make s` |
| Baseline validation bundle | `make validate` | `make v` |
| CI-parity baseline bundle | `make ci` | _n/a_ |

Notes:

- `make stack` includes infra boundary-file presence checks by default.
- Set `VALIDATE_INFRA=0` when reusing this repository pattern where infra
  boundary files are intentionally out of scope.

## CI parity mapping for local runs

Use this table to mirror CI behavior before opening a PR:

| CI workflow job | CI command | Local equivalent |
| --- | --- | --- |
| `python-tests` | `pytest -q --junitxml artifacts/ci/pytest-junit.xml` | `make t` |
| `readme-anchor-check` | `python scripts/check_readme_anchors.py` | `make g` |
| `tech-stack-check` | `python scripts/check_tech_stack.py` | `make s` |
| _deployment-readiness subset_ | file existence checks in runbook checklist | `make s` |
| _combined local baseline_ | multiple jobs above | `make ci` (or `make v`) |

For full CI workflow coverage (including markdown lint, YAML validation, secret
scan, and governance gate artifact checks), refer to `.github/workflows/ci.yml`.

## Optional pre-commit hook installation

DX-003 adds an optional local pre-commit baseline that runs fast checks before
commits:

- `make g` (README/governance anchor validation)
- `make s` (runtime stack declaration + deployment-readiness file checks)

Install and use the hooks:

```bash
python -m pip install pre-commit
pre-commit install --hook-type pre-commit
pre-commit run --all-files
```

Uninstall hooks (if needed):

```bash
pre-commit uninstall
```

The hook definitions live in `.pre-commit-config.yaml` and are intentionally
limited to quick checks; keep `make v`/`make ci` in your normal PR workflow for
full baseline validation.
