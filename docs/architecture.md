# Architecture Overview

This repository documents an agent-driven, modular pressure vessel design platform.

Primary concerns:

- Requirements capture and normalization

- Standards-aware calculation services

- Compliance traceability and report generation

- Human-in-the-loop governance and approvals

## BL-006 Traceability Graph

- Schema: `TraceabilityGraphRevision.v1` with immutable, revision-scoped link snapshots.
- Link endpoints: requirement, clause, model, calculation, artifact, approval.
- Audit helpers support revision-scoped and clause-scoped evidence retrieval and report templating.
