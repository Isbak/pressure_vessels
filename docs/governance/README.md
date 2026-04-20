# Governance Artifacts

This folder contains policy-as-data artifacts used by CI governance checks.

## Files

- `ci_governance_policy.v1.json`: required CI gate definitions and retention policy.
- `policy_exceptions_schema.v1.json`: JSON Schema for approved governance gate exceptions.

## Policy wiring requirements

`ci_governance_policy.v1.json` is the single source of truth for CI artifact retention (`artifact_retention_days`).
Workflow jobs that upload artifacts must read this value from the policy file and pass it through to
`actions/upload-artifact` rather than hard-coding retention values in workflow YAML.
Any workflow update must preserve this linkage.

`required_gates` in `ci_governance_policy.v1.json` is also enforced as the control-plane source of truth.
`pv-check-ci-governance` fails closed when CI emits gates not listed in policy or omits required
policy gates, preventing silent governance/CI drift.

## Reusing the governance checks in another repository

After installing this package (`pip install -e .` locally or `pip install pressure_vessels` from a release),
use the packaged entry points instead of repository-local script paths:

```bash
pv-check-ci-governance \
  path/to/ci_governance_policy.v1.json \
  path/to/policy_exceptions.v1.json \
  path/to/job-results.json \
  path/to/GovernanceGateReport.v1.json \
  --exceptions-schema path/to/policy_exceptions_schema.v1.json

pv-generate-governance-checklist-evidence \
  path/to/job-results.json \
  path/to/GovernanceGateReport.v1.json \
  path/to/GovernanceChecklistEvidence.v1.json
```

The schema path for exceptions is an explicit CLI input so adopters can keep policy documents in
repository-specific locations without patching Python source.

## Exception workflow

Exception request, review, and expiration handling are defined in `AGENT_GOVERNANCE.md` §11 "Exception Request & Approval Workflow".

All approved exceptions must be recorded in `.github/governance/policy_exceptions.v1.json` and validate against `policy_exceptions_schema.v1.json`.
