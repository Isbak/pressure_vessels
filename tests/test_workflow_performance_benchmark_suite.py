from __future__ import annotations

import json
from pathlib import Path

from pressure_vessels.performance_benchmark_suite import (
    BenchmarkScenario,
    build_profile_artifact_bundle,
    run_workflow_performance_benchmark_suite,
    write_benchmark_artifact_bundle,
)


def test_benchmark_suite_reports_concurrency_latency_and_throughput() -> None:
    report = run_workflow_performance_benchmark_suite(
        scenarios=(
            BenchmarkScenario(
                scenario_id="test_scale_x2",
                description="Deterministic unit-test scenario.",
                concurrent_workers=2,
                runs_per_worker=2,
            ),
        ),
    )

    assert report["schema_version"] == "WorkflowPerformanceBenchmarkReport.v1"
    assert report["summary"]["all_scenarios_passed"] is True
    scenario_report = report["scenario_reports"][0]
    assert scenario_report["summary"]["throughput_runs_per_second"] > 0
    assert scenario_report["summary"]["latency_ms"]["p95"] >= scenario_report["summary"]["latency_ms"]["p50"]
    assert report["capacity_envelope"]["max_safe_workers"] == 2
    assert report["capacity_envelope"]["recommended_sustained_workers"] == 1


def test_profile_bundle_and_artifact_outputs_are_ci_retention_friendly(tmp_path: Path) -> None:
    report = run_workflow_performance_benchmark_suite()
    bundle = build_profile_artifact_bundle(report)

    assert bundle["schema_version"] == "WorkflowProfileArtifactBundle.v1"
    assert bundle["bottlenecks"]
    assert bundle["mitigation_recommendations"]

    output_paths = write_benchmark_artifact_bundle(
        output_directory=tmp_path,
        benchmark_report=report,
        profile_bundle=bundle,
    )

    for path in output_paths.values():
        assert path.exists()

    benchmark_json = json.loads(output_paths["benchmark_report"].read_text(encoding="utf-8"))
    profile_json = json.loads(output_paths["profile_bundle"].read_text(encoding="utf-8"))

    assert benchmark_json["capacity_envelope"]["max_tested_workers"] >= benchmark_json["capacity_envelope"][
        "recommended_sustained_workers"
    ]
    assert "safe_operating_guidance" in benchmark_json["capacity_envelope"]
    assert profile_json["bottlenecks"][0]["stage_id"]
    assert "Workflow Benchmark Mitigation Notes" in output_paths["mitigation_notes"].read_text(encoding="utf-8")
    assert "Workflow Capacity Envelope Report" in output_paths["capacity_envelope_report"].read_text(
        encoding="utf-8"
    )
