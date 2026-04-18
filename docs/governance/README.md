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

## Exception workflow

Exception request, review, and expiration handling are defined in `AGENT_GOVERNANCE.md` §11 "Exception Request & Approval Workflow".

All approved exceptions must be recorded in `.github/governance/policy_exceptions.v1.json` and validate against `policy_exceptions_schema.v1.json`.
