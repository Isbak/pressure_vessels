# Governance Artifacts

This folder contains policy-as-data artifacts used by CI governance checks.

## Files

- `ci_governance_policy.v1.json`: required CI gate definitions and retention policy.
- `policy_exceptions_schema.v1.json`: JSON Schema for approved governance gate exceptions.

## Exception workflow

Exception request, review, and expiration handling are defined in `AGENT_GOVERNANCE.md` §11 "Exception Request & Approval Workflow".

All approved exceptions must be recorded in `.github/governance/policy_exceptions.v1.json` and validate against `policy_exceptions_schema.v1.json`.
