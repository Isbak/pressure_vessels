# Runbook: BL-005 / BL-036 Standards Ingestion Pipeline

## Purpose

Operational runbook for producing immutable, versioned `StandardsPackage.v1` artifacts with lifecycle promotions and migration checks.

## Inputs

- One or more `StandardSource` records with source metadata and clause text.
- `standard_key` (for example `ASME_VIII_1`)
- `standard_version` (for example `2025.2`)
- `release_label` (for example `r1`)
- One or more `RegressionExample` records.
- Optional baseline `StandardsPackage` for migration checks.
- Optional `ProjectClauseDependency` list to generate selective re-verification scope.

## Procedure

1. Build source list from licensed standards content.
2. Define regression examples that assert required clauses and required clause links.
3. Run `run_standards_ingestion(...)`.
4. Confirm all regression examples pass.
5. Persist the package with `write_standards_package(...)`.
6. Store output package under controlled artifact storage.
7. Promote lifecycle stage with `promote_standards_package(...)`:
   - `draft -> candidate` requires engineering reviewer approval.
   - `candidate -> released` requires engineering + domain approvals.
8. If baseline package is provided, review:
   - `cross_version_regression` for clause/link drift.
   - `impact_analysis` for affected projects and selective re-verification scope.

## Deterministic Controls

- Inject `now_utc` for reproducible timestamps in tests.
- Clauses are sorted by `clause_id`.
- Semantic links are sorted by `(from_clause_id, to_clause_id, link_type)`.
- Hashes use sha256 over canonical JSON (`sort_keys=True`, compact separators).
- Package publish is atomic: writes are staged in a sibling temp file
  (`<target>.tmp.<uuid>`), fsynced, and then published via `os.replace`.

## Failure Modes (Fail Closed)

- Missing source metadata or source text.
- Malformed source lines that do not match `CLAUSE-ID: clause body`.
- Duplicate clause IDs in source content.
- No parseable clause rows found in source text.
- Parsed/normalized mismatch.
- Semantic links to unknown clauses.
- Missing/failed regression examples.
- Invalid lifecycle stage or missing required stage approvals.
- Non-sequential lifecycle transition attempts.
- Release stage with baseline package where cross-version drift is detected.
- Duplicate package write path (immutable package overwrite attempt), raised as
  `StandardsPackageCollisionError` naming the `package_id` and colliding path.

## Example Snippet

```python
from datetime import datetime, timezone
from pressure_vessels.standards_ingestion_pipeline import (
    RegressionExample,
    StandardSource,
    run_standards_ingestion,
    write_standards_package,
)

package = run_standards_ingestion(
    source_documents=[
        StandardSource(
            source_id="ASME_BPVC_VIII_DIV1_2025_MAIN",
            title="ASME BPVC Section VIII Division 1 (sample)",
            publisher="ASME",
            edition="2025",
            revision="2025.2",
            content_text="UG-16: Minimum thickness...\nUG-27: ... See UG-16.",
        )
    ],
    standard_key="ASME_VIII_1",
    standard_version="2025.2",
    release_label="r1",
    regression_examples=[
        RegressionExample(
            example_id="REG-001",
            required_clause_ids=["UG-16", "UG-27"],
            required_link_pairs=[("UG-27", "UG-16")],
        )
    ],
    now_utc=datetime(2026, 4, 18, tzinfo=timezone.utc),
)

write_standards_package(package, "artifacts/bl-005")
```
