from __future__ import annotations

import json
from pathlib import Path

from pressure_vessels.qa_benchmark_pipeline import (
    QA_BENCHMARK_DATASET_MANIFEST_VERSION,
    QA_QUALITY_GATE_REPORT_VERSION,
    load_benchmark_dataset_manifest,
    run_cross_verification_harness,
    write_quality_gate_report,
)


def test_benchmark_manifest_is_versioned_and_references_existing_fixtures() -> None:
    manifest_path = Path("tests/golden_examples/benchmark_manifest.json")
    manifest = load_benchmark_dataset_manifest(manifest_path)

    assert manifest.schema_version == QA_BENCHMARK_DATASET_MANIFEST_VERSION
    categories = {case.category for case in manifest.cases}
    assert {"golden", "boundary", "stress", "reject"}.issubset(categories)

    for case in manifest.cases:
        assert (Path(case.fixture_path)).exists(), f"Missing fixture for {case.case_id}"


def test_cross_verification_harness_is_deterministic_and_passing() -> None:
    repo_root = Path(".")
    manifest_path = Path("tests/golden_examples/benchmark_manifest.json")
    manifest = load_benchmark_dataset_manifest(manifest_path)

    report_a = run_cross_verification_harness(manifest, manifest_path=manifest_path, repo_root=repo_root)
    report_b = run_cross_verification_harness(manifest, manifest_path=manifest_path, repo_root=repo_root)

    assert report_a == report_b
    assert report_a["schema_version"] == QA_QUALITY_GATE_REPORT_VERSION
    assert report_a["overall_status"] == "pass"
    assert report_a["summary"]["fail_cases"] == 0
    assert report_a["summary"]["total_check_failures"] == 0


def test_quality_gate_report_artifact_is_written_with_stable_payload(tmp_path: Path) -> None:
    manifest_path = Path("tests/golden_examples/benchmark_manifest.json")
    manifest = load_benchmark_dataset_manifest(manifest_path)
    report = run_cross_verification_harness(manifest, manifest_path=manifest_path, repo_root=Path("."))

    artifact_path = tmp_path / "quality-gate-report.json"
    write_quality_gate_report(report, artifact_path)

    persisted = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert persisted == report
    assert persisted["overall_status"] == "pass"
    reject_case = next(case for case in persisted["case_results"] if case["category"] == "reject")
    assert reject_case["calculation_hash"] is None
    assert all("observed_error" in result for result in reject_case["check_results"])
