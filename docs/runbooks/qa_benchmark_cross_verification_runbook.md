# QA Benchmark Cross-Verification Runbook (BL-017)

## Scope

Operational steps for running and validating BL-017 benchmark quality gates locally and in CI.

## Deterministic inputs

- Manifest: `tests/golden_examples/benchmark_manifest.json`
- Fixture set: `tests/golden_examples/example_*.json`
- Fixed timestamp is provided by manifest (`deterministic_timestamp_utc`).

## Local execution

1. Run benchmark coverage:
   - `PYTHONPATH=src pytest tests/test_calculation_pipeline_golden_examples.py tests/test_qa_benchmark_harness.py`
2. Generate retained report artifact:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from pressure_vessels.qa_benchmark_pipeline import (
    load_benchmark_dataset_manifest,
    run_cross_verification_harness,
    write_quality_gate_report,
)

manifest_path = Path("tests/golden_examples/benchmark_manifest.json")
manifest = load_benchmark_dataset_manifest(manifest_path)
report = run_cross_verification_harness(manifest, manifest_path=manifest_path, repo_root=Path("."))
write_quality_gate_report(report, Path("artifacts/bl-017/qa_quality_gate_report.v1.json"))
PY
```

## Expected outcomes

- All cases pass (`overall_status = pass`).
- Boundary and stress categories are present in manifest and report.
- Artifact is retained at `artifacts/bl-017/qa_quality_gate_report.v1.json` for audit traceability.
