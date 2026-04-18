# Runbook: BL-005 Standards Ingestion Pipeline

## Purpose

Operational runbook for producing immutable, versioned `StandardsPackage.v1` artifacts.

## Inputs

- One or more `StandardSource` records with source metadata and clause text.
- `standard_key` (for example `ASME_VIII_1`)
- `standard_version` (for example `2025.2`)
- `release_label` (for example `r1`)
- One or more `RegressionExample` records.

## Procedure

1. Build source list from licensed standards content.
2. Define regression examples that assert required clauses and required clause links.
3. Run `run_standards_ingestion(...)`.
4. Confirm all regression examples pass.
5. Persist the package with `write_standards_package(...)`.
6. Store output package under controlled artifact storage.

## Deterministic Controls

- Inject `now_utc` for reproducible timestamps in tests.
- Clauses are sorted by `clause_id`.
- Semantic links are sorted by `(from_clause_id, to_clause_id, link_type)`.
- Hashes use sha256 over canonical JSON (`sort_keys=True`, compact separators).

## Failure Modes (Fail Closed)

- Missing source metadata or source text.
- No parseable clause rows found in source text.
- Parsed/normalized mismatch.
- Semantic links to unknown clauses.
- Missing/failed regression examples.
- Duplicate package write path (immutable package overwrite attempt).

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
