# Developer Command Reference

This reference defines short local task aliases for common workflows and maps
them to equivalent CI checks.

## Local task runner commands

Run from repository root:

| Workflow | Standard command | Short alias |
| --- | --- | --- |
| Bootstrap local Python + JS dependencies | `make bootstrap` | _n/a_ |
| Unit tests | `make test` | `make t` |
| Governance docs/anchor checks | `make governance` | `make g` |
| Runtime stack checks | `make stack` | `make s` |
| JS service validation checks | `make validate-js` | _n/a_ |
| Baseline validation bundle | `make validate` | `make v` |
| Local runtime integration profile up | `make integration-up` | `make up` |
| Local runtime integration profile down | `make integration-down` | `make down` |
| Local runtime integration profile logs | `make integration-logs` | `make logs` |
| CI-parity baseline bundle | `make ci` | _n/a_ |

Notes:

- `make stack` includes infra boundary-file presence checks by default.
- Set `VALIDATE_INFRA=0` when reusing this repository pattern where infra
  boundary files are intentionally out of scope.
- `make bootstrap` fails fast when `node`/`npm` are missing and installs
  dependencies for both `services/frontend` and `services/backend`.
- `make validate` includes `make validate-js`, which runs
  `npm --prefix services/frontend run smoke` and
  `npm --prefix services/backend run smoke`.
- JS checks fail fast when `node`/`npm` are missing; set `JS_VALIDATE=0` to
  explicitly skip JS checks in local environments without Node tooling.

## CI parity mapping for local runs

Use this table to mirror CI behavior before opening a PR:

| CI workflow job | CI command | Local equivalent |
| --- | --- | --- |
| `python-tests` | `pytest -q --junitxml artifacts/ci/pytest-junit.xml` | `make t` |
| `readme-anchor-check` | `python scripts/check_readme_anchors.py` | `make g` |
| `tech-stack-check` | `python scripts/check_tech_stack.py` | `make s` |
| `js-validate` | `make validate-js` | `make validate-js` |
| _deployment-readiness subset_ | file existence checks in runbook checklist | `make s` |
| _combined local baseline_ | `python-tests` + `readme-anchor-check` + `tech-stack-check` + `js-validate` | `make ci` (or `make v`) |

For full CI workflow coverage (including markdown lint, YAML validation, secret
scan, governance gate artifact checks, and governance checklist evidence generation), refer to `.github/workflows/ci.yml`.

Governance checklist evidence generated in CI is published in the `governance-gate-report` artifact bundle as `artifacts/ci/GovernanceChecklistEvidence.v1.json`.

## PR risk label suggestion workflow (DX-008)

CI includes an advisory `risk-label-suggestion` job on pull requests. It uses
changed-file heuristics aligned to `AGENT_GOVERNANCE.md#4-change-classification-and-merge-gates`
to suggest `low` / `medium` / `high` risk labels.

Heuristic routing baseline:

- **High** suggestion: compliance calculation paths, CI/governance control files,
  or infrastructure-as-code primitives change.
- **Medium** suggestion: application code, tests, scripts, or developer tooling
  manifests change.
- **Low** suggestion: docs/artifact metadata-only changes.

Outputs and visibility:

- PR workflow job summary includes the suggested risk and matched paths.
- Artifact bundle `risk-label-suggestion` includes:
  - `artifacts/ci/RiskLabelSuggestion.v1.json`
  - `artifacts/ci/RiskLabelSuggestion.summary.md`
  - `artifacts/ci/changed-paths.txt`

Important: this job is **advisory only** and has no merge authority. Human
reviewers remain responsible for final risk classification and approval routing.

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

## Local runtime integration profile (DX-006)

Use the Docker Compose profile at `infra/local/docker-compose.integration.yml` for a one-command frontend/backend startup:

```bash
make integration-up
```

Environment variables used by the integration profile:

| Variable | Default | Used by | Purpose |
| --- | --- | --- | --- |
| `FRONTEND_PORT` | `3000` | frontend container + host port map | Host/browser entrypoint for Next.js dev server. |
| `BACKEND_PORT` | `8000` | backend container + host port map | Host API port for backend health and prompt routes. |
| `BACKEND_API_BASE_URL` | `http://backend:8000` | frontend container | Internal Docker-network backend URL used by frontend BFF route. |
| `BACKEND_HOST` | `0.0.0.0` | backend container | Bind address for backend local integration server. |

Service dependencies and ownership boundaries:

- `frontend` depends on `backend` health status before startup, matching frontend→backend ownership boundaries in the runtime operations runbook.
- `frontend` has no direct datastore wiring in this local profile (backend is the only data-plane boundary).

For startup issues and recovery commands, see `docs/runbooks/local_runtime_integration_troubleshooting.md`.
