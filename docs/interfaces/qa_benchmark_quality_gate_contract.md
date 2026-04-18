# QA Benchmark Quality Gate Contract (BL-017)

## Purpose

Defines the deterministic dataset manifest and quality-gate report contract for benchmark and cross-verification CI checks.

## Dataset manifest

- Path: `tests/golden_examples/benchmark_manifest.json`
- Schema version: `QABenchmarkDatasetManifest.v1`
- Required fields:
  - `manifest_id`
  - `deterministic_timestamp_utc` (RFC3339 UTC)
  - `benchmark_prompt`
  - `cases[]` with:
    - `case_id`
    - `fixture_path`
    - `category` (`golden`, `boundary`, `stress`)
    - `description`

## Quality-gate report

- Schema version: `QABenchmarkQualityGateReport.v1`
- Produced by `pressure_vessels.qa_benchmark_pipeline.run_cross_verification_harness`
- Required sections:
  - `manifest` (id/path/schema/hash)
  - `summary` (`total_cases`, `pass_cases`, `fail_cases`, `total_check_failures`)
  - `overall_status` (`pass` | `fail`)
  - `case_results[]` with deterministic per-case hash and per-check comparison fields
  - top-level `deterministic_hash`

## CI integration expectations

- CI executes pytest cases that invoke the harness.
- CI writes a report artifact to `artifacts/bl-017/qa_quality_gate_report.v1.json`.
- Any non-zero `fail_cases` or `total_check_failures` must fail the quality gate.
