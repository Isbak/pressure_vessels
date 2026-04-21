# Workflow Orchestrator Performance & Scale Benchmark Runbook (BL-040)

This runbook defines deterministic benchmark execution for concurrent workflow orchestration paths and captures CI-retained profiling artifacts.

## Scope

- Benchmark harness module: `src/pressure_vessels/performance_benchmark_suite.py`
- Artifact outputs (CI-friendly):
  - `workflow_performance_benchmark_report.json`
  - `workflow_profile_artifact_bundle.json`
  - `workflow_benchmark_mitigation_notes.md`
  - `workflow_capacity_envelope_report.md`

## Local or CI Execution

```bash
PYTHONPATH=src python -c "from pathlib import Path; from pressure_vessels.performance_benchmark_suite import run_workflow_performance_benchmark_suite, build_profile_artifact_bundle, write_benchmark_artifact_bundle; report = run_workflow_performance_benchmark_suite(); bundle = build_profile_artifact_bundle(report); write_benchmark_artifact_bundle(output_directory=Path('artifacts/bl040'), benchmark_report=report, profile_bundle=bundle)"
```

## Profiling artifacts and mitigation workflow

1. Retain the generated JSON/Markdown files as CI artifacts.
2. Review `workflow_profile_artifact_bundle.json` bottlenecks sorted by stage latency and retry saturation.
3. Track mitigation recommendations from `workflow_benchmark_mitigation_notes.md` in the next sprint if saturation exceeds 0.70 for any critical stage.

## Capacity envelope and safe operating guidance

Validated deterministic envelope in this suite:

- Maximum tested concurrent workers: 4
- Maximum safe concurrent workers: 4
- Recommended sustained workers: 2
- Guidance: stay at or below sustained workers for continuous operation; reserve remaining headroom for incident response and burst retries.

If future changes alter retry behavior or stage composition, rerun the benchmark suite and publish a refreshed capacity envelope report in CI artifacts.
