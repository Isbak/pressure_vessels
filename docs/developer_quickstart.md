# Developer Quickstart (10 Minutes)

This quickstart provides a single command for local environment bootstrap and a
single command for baseline validation, aligned with the repository governance
baseline.

## Scope

- Audience: first-time contributors and maintainers validating a local checkout.
- Goal: reach a reproducible baseline quickly without bypassing governance.
- Ownership boundaries: this quickstart covers repository bootstrap/validation
  only; module behavior and architecture responsibilities remain defined in
  `README.md` under **System Architecture (Modular)**.

## Optional fast path: Dev Container / GitHub Codespaces

Use this path when you want one-click onboarding with pinned toolchains
(Python 3.11 + Node 20) without installing them on your host machine.

1. Open the repository in a Dev Container (VS Code: **Reopen in Container**) or
   in GitHub Codespaces.
2. Wait for the container build and `postCreateCommand` to complete. The
   container automatically runs `make bootstrap` on first create.
3. From the repository root inside the container, run:

```bash
make bootstrap && make validate
```

Notes:
- The devcontainer configuration is committed at `.devcontainer/devcontainer.json`.
- Docker CLI support is included in-container for optional integration-profile
  workflows; replacing existing Docker Compose profile flows is out of scope
  for this DX item.

## Prerequisites

- `make` (GNU Make 3.81+ recommended)
- Python 3.11+
- `pip`
- Node.js 20.x or newer (with `npm`); `tools/versions.json` defines the
  minimum supported major

## 1) Bootstrap (single command)

Run from the repository root:

```bash
make bootstrap
```

What it does:

- Upgrades `pip`
- Installs the package in editable mode
- Installs `pytest` for local baseline checks
- Verifies that the Node.js toolchain is present and meets the minimum major
  version in `tools/versions.json` before any JS install work
- Installs frontend dependencies (`services/frontend/package.json`)
- Installs backend dependencies (`services/backend/package.json`)

Override variables when needed:

- `PYTHON` (default: `python`)
- `PIP` (default: `pip`)
- `NPM` (default: `npm`)

## 2) Baseline validation (single command)

Run from the repository root:

```bash
make validate
```

What it checks:

- Unit tests (`pytest -q`)
- Tech stack documentation consistency (`pv-check-tech-stack` via `make s`)
- README anchor consistency for backlog references
  (`pv-check-readme-anchors` via `make g`)
- Runtime foundation boundary files exist for core infra modules:
  - environment bootstrap + IaC primitives
  - secrets + observability
  - postgresql + redis + runtime
  - keycloak + temporal
  - neo4j + qdrant + opensearch
  - vLLM + model catalog
- Python style baseline (`python scripts/check_python_style.py`)
- JS/TS style baseline (`python scripts/check_js_ts_style.py`)

Override variables when needed:

- `VALIDATE_INFRA=0` to skip infra boundary checks for non-platform projects
- `INFRA_BOUNDARY_MANIFEST=/path/to/project-boundary-files.manifest` to point
  at a project-specific boundary file manifest (one path per line)
- `INFRA_BOUNDARY_FILES="..."` to pass an explicit space-delimited file list
  (legacy override compatibility)

## Governance checks to keep in view

This quickstart is intentionally mapped to core governance controls in
`AGENT_GOVERNANCE.md`:

- **Required controls baseline**: keep tests and repository policy checks
  passing before opening a PR.
- **Standard workflow**: plan, implement, cross-check, and human review still
  apply even for documentation-first changes.
- **Starter governance checklist**: ensure PR metadata includes risk class,
  test evidence, and required approvals.

For CI-specific governance gate enforcement details, see:

- `.github/workflows/ci.yml`
- `scripts/check_ci_governance.py`
- `docs/governance/ci_governance_policy.v1.json`
- `docs/developer_command_reference.md` (local aliases + CI parity map)

For infra ownership and deployment-readiness context, see
`docs/runbooks/platform_runtime_stack_operations.md`.

## Reusing this DX baseline in other projects

To apply this workflow in other repositories while preserving governance-by-default,
use the baseline scaffold command instead of manually copying files:

```bash
pv-scaffold-governance-baseline --target /path/to/target-repo
```

What this scaffolds:

- `AGENT_GOVERNANCE.md`
- `docs/governance/ci_governance_policy.v1.json`
- `docs/governance/policy_exceptions_schema.v1.json`
- `docs/governance/risk_label_heuristics.v1.json`
- `.github/workflows/reusable-governance-core.yml`
- `scripts/check_ci_governance.py`

The command also writes `.governance/baseline_source.v1.json` with source repository,
baseline version, commit SHA, generation timestamp, and per-file SHA-256 values so
downstream repositories can track drift from this baseline.

After scaffolding, wire your project-specific paths and commands:

1. Keep `validate` as the single local baseline command.
2. Point `INFRA_BOUNDARY_MANIFEST` at that project's boundary-file manifest.
3. Keep policy checks in `validate` aligned with CI-required checks.
4. If infra does not apply, set `VALIDATE_INFRA=0` and document why in the
   project quickstart.

For CI reuse, prefer calling the reusable governance workflow and pass your
repository paths as inputs (instead of forking the full CI file). Example:

```yaml
jobs:
  governance-gate:
    needs:
      - docs-check
      - markdown-lint
      - python-tests
    uses: pressure-vessels/pressure_vessels/.github/workflows/reusable-governance-core.yml@main
    with:
      backlog_path: docs/development_backlog.yaml
      tech_stack_registry_path: docs/platform_runtime_stack_registry.yaml
      environment_bootstrap_path: infra/platform/environment.bootstrap.yaml
      policy_backlog_path: docs/governance/policy_backlog.yaml
      ci_policy_path: docs/governance/ci_governance_policy.v1.json
      policy_exceptions_path: .github/governance/policy_exceptions.v1.json
      exceptions_schema_path: docs/governance/policy_exceptions_schema.v1.json
      upstream_needs_json: ${{ toJson(needs) }}
```
