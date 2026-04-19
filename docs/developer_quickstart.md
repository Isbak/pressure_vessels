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

## Prerequisites

- `make` (GNU Make 3.81+ recommended)
- Python 3.11+
- `pip`

## 1) Bootstrap (single command)

Run from the repository root:

```bash
make bootstrap
```

What it does:

- Upgrades `pip`
- Installs the package in editable mode
- Installs `pytest` for local baseline checks

Override variables when needed:

- `PYTHON` (default: `python`)
- `PIP` (default: `pip`)

## 2) Baseline validation (single command)

Run from the repository root:

```bash
make validate
```

What it checks:

- Unit tests (`pytest -q`)
- Tech stack documentation consistency (`scripts/check_tech_stack.py`)
- README anchor consistency for backlog references
  (`scripts/check_readme_anchors.py`)
- Runtime foundation boundary files exist for core infra modules:
  - environment bootstrap + IaC primitives
  - secrets + observability
  - postgresql + redis + runtime
  - keycloak + temporal
  - neo4j + qdrant + opensearch
  - vLLM + model catalog

Override variables when needed:

- `VALIDATE_INFRA=0` to skip infra boundary checks for non-platform projects
- `INFRA_BOUNDARY_FILES="..."` to provide a project-specific infra file list

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

To apply this workflow in other repositories while preserving governance-by-default:

1. Copy the `Makefile` bootstrap/validate targets.
2. Keep `validate` as the single local baseline command.
3. Point `INFRA_BOUNDARY_FILES` at that project's boundary manifests.
4. Keep policy checks in `validate` aligned with CI-required checks.
5. If infra does not apply, set `VALIDATE_INFRA=0` and document why in the
   project quickstart.
