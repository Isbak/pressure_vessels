"""BL-040 deterministic performance and scale benchmark suite for workflow orchestration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
from pathlib import Path
from statistics import mean
from typing import Any

from .workflow_orchestrator import WorkflowStageSpec, build_approval_gate_event, orchestrate_workflow

WORKFLOW_PERFORMANCE_BENCHMARK_REPORT_VERSION = "WorkflowPerformanceBenchmarkReport.v1"
WORKFLOW_PROFILE_ARTIFACT_BUNDLE_VERSION = "WorkflowProfileArtifactBundle.v1"
WORKFLOW_CAPACITY_ENVELOPE_REPORT_VERSION = "WorkflowCapacityEnvelopeReport.v1"


@dataclass(frozen=True)
class BenchmarkScenario:
    scenario_id: str
    description: str
    concurrent_workers: int
    runs_per_worker: int


DEFAULT_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    BenchmarkScenario(
        scenario_id="baseline_x1",
        description="Single-worker deterministic baseline.",
        concurrent_workers=1,
        runs_per_worker=3,
    ),
    BenchmarkScenario(
        scenario_id="scale_x2",
        description="Two concurrent workers under nominal load.",
        concurrent_workers=2,
        runs_per_worker=3,
    ),
    BenchmarkScenario(
        scenario_id="scale_x4",
        description="Four concurrent workers with bounded retries.",
        concurrent_workers=4,
        runs_per_worker=3,
    ),
)


def run_workflow_performance_benchmark_suite(
    *,
    scenarios: tuple[BenchmarkScenario, ...] = DEFAULT_SCENARIOS,
    deterministic_timestamp_utc: str = "2026-04-21T00:00:00+00:00",
) -> dict[str, Any]:
    scenario_reports = [
        _run_scenario(scenario=scenario, deterministic_timestamp_utc=deterministic_timestamp_utc)
        for scenario in scenarios
    ]

    max_safe_workers = max(
        report["scenario"]["concurrent_workers"]
        for report in scenario_reports
        if report["summary"]["success_ratio"] == 1.0
    )
    recommended_sustained_workers = max(1, max_safe_workers // 2)

    return {
        "schema_version": WORKFLOW_PERFORMANCE_BENCHMARK_REPORT_VERSION,
        "deterministic_timestamp_utc": deterministic_timestamp_utc,
        "summary": {
            "scenario_count": len(scenario_reports),
            "all_scenarios_passed": all(report["summary"]["success_ratio"] == 1.0 for report in scenario_reports),
        },
        "scenario_reports": scenario_reports,
        "capacity_envelope": {
            "max_tested_workers": max(report["scenario"]["concurrent_workers"] for report in scenario_reports),
            "max_safe_workers": max_safe_workers,
            "recommended_sustained_workers": recommended_sustained_workers,
            "safe_operating_guidance": (
                "Operate at or below recommended_sustained_workers to keep modeled retry saturation "
                "below 0.70 and preserve headroom for incident handling."
            ),
        },
    }


def build_profile_artifact_bundle(benchmark_report: dict[str, Any]) -> dict[str, Any]:
    stage_profiles: list[dict[str, Any]] = []
    for scenario in benchmark_report["scenario_reports"]:
        for row in scenario["stage_profiles"]:
            stage_profiles.append(
                {
                    "scenario_id": scenario["scenario"]["scenario_id"],
                    "stage_id": row["stage_id"],
                    "avg_stage_latency_ms": row["avg_stage_latency_ms"],
                    "avg_retry_saturation_ratio": row["avg_retry_saturation_ratio"],
                }
            )

    bottlenecks = sorted(
        stage_profiles,
        key=lambda row: (row["avg_stage_latency_ms"], row["avg_retry_saturation_ratio"]),
        reverse=True,
    )[:5]

    recommendations = [
        {
            "stage_id": row["stage_id"],
            "scenario_id": row["scenario_id"],
            "recommendation": _mitigation_for_stage(row["stage_id"]),
        }
        for row in bottlenecks
    ]

    return {
        "schema_version": WORKFLOW_PROFILE_ARTIFACT_BUNDLE_VERSION,
        "benchmark_schema_version": benchmark_report["schema_version"],
        "bottlenecks": bottlenecks,
        "mitigation_recommendations": recommendations,
    }


def write_benchmark_artifact_bundle(
    *,
    output_directory: Path,
    benchmark_report: dict[str, Any],
    profile_bundle: dict[str, Any],
) -> dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)

    benchmark_report_path = output_directory / "workflow_performance_benchmark_report.json"
    benchmark_report_path.write_text(
        json.dumps(benchmark_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    profile_bundle_path = output_directory / "workflow_profile_artifact_bundle.json"
    profile_bundle_path.write_text(
        json.dumps(profile_bundle, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    mitigation_path = output_directory / "workflow_benchmark_mitigation_notes.md"
    mitigation_lines = [
        "# Workflow Benchmark Mitigation Notes",
        "",
        f"- Schema version: `{profile_bundle['schema_version']}`",
        f"- Bottlenecks identified: `{len(profile_bundle['bottlenecks'])}`",
        "",
    ]
    for recommendation in profile_bundle["mitigation_recommendations"]:
        mitigation_lines.append(
            "- "
            f"`{recommendation['scenario_id']}` / `{recommendation['stage_id']}`: "
            f"{recommendation['recommendation']}"
        )
    mitigation_path.write_text("\n".join(mitigation_lines) + "\n", encoding="utf-8")

    capacity_report_path = output_directory / "workflow_capacity_envelope_report.md"
    envelope = benchmark_report["capacity_envelope"]
    capacity_report_path.write_text(
        "\n".join(
            [
                "# Workflow Capacity Envelope Report",
                "",
                f"- Schema version: `{WORKFLOW_CAPACITY_ENVELOPE_REPORT_VERSION}`",
                f"- Maximum tested concurrent workers: `{envelope['max_tested_workers']}`",
                f"- Maximum safe concurrent workers: `{envelope['max_safe_workers']}`",
                f"- Recommended sustained workers: `{envelope['recommended_sustained_workers']}`",
                f"- Safe operating guidance: {envelope['safe_operating_guidance']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "benchmark_report": benchmark_report_path,
        "profile_bundle": profile_bundle_path,
        "mitigation_notes": mitigation_path,
        "capacity_envelope_report": capacity_report_path,
    }


def _run_scenario(*, scenario: BenchmarkScenario, deterministic_timestamp_utc: str) -> dict[str, Any]:
    run_count = scenario.concurrent_workers * scenario.runs_per_worker
    with ThreadPoolExecutor(max_workers=scenario.concurrent_workers) as executor:
        reports = list(
            executor.map(
                lambda index: _execute_workflow_run(
                    scenario_id=scenario.scenario_id,
                    run_index=index,
                    deterministic_timestamp_utc=deterministic_timestamp_utc,
                ),
                range(1, run_count + 1),
            )
        )

    latencies_ms = sorted(report["workflow_latency_ms"] for report in reports)
    successes = sum(1 for report in reports if report["status"] == "completed")
    modeled_total_seconds = max(0.001, sum(latencies_ms) / 1000.0)

    return {
        "scenario": {
            "scenario_id": scenario.scenario_id,
            "description": scenario.description,
            "concurrent_workers": scenario.concurrent_workers,
            "runs_per_worker": scenario.runs_per_worker,
        },
        "summary": {
            "total_runs": run_count,
            "successful_runs": successes,
            "success_ratio": successes / float(run_count),
            "throughput_runs_per_second": round(successes / modeled_total_seconds, 3),
            "latency_ms": {
                "p50": _percentile(latencies_ms, 0.50),
                "p95": _percentile(latencies_ms, 0.95),
                "max": latencies_ms[-1],
            },
        },
        "stage_profiles": _summarize_stage_profiles(reports),
    }


def _execute_workflow_run(*, scenario_id: str, run_index: int, deterministic_timestamp_utc: str) -> dict[str, Any]:
    workflow_id = f"wf-bl040-{scenario_id}-{run_index:03d}"
    approval = build_approval_gate_event(
        event_id=f"APR-BL040-{scenario_id}-{run_index:03d}",
        workflow_id=workflow_id,
        stage_id="compliance_review",
        gate_id="human_approval",
        decision="approved",
        approver_role="authorized_inspector",
        approver_id="inspector-bl040",
        decided_at_utc=deterministic_timestamp_utc,
        rationale="Deterministic benchmark approval.",
    )
    report = orchestrate_workflow(
        workflow_id=workflow_id,
        stage_specs=[
            WorkflowStageSpec(stage_id="prepare_inputs", requires_approval=False),
            WorkflowStageSpec(stage_id="compliance_review", requires_approval=True),
            WorkflowStageSpec(stage_id="artifact_export", requires_approval=False, max_retries=2, fail_first_attempts=1),
        ],
        approval_events=[approval],
    )

    stage_latency_by_stage = {
        metric.stage_id: metric.value
        for metric in report.telemetry_metric_events
        if metric.metric_name == "stage_latency_ms"
    }
    retry_saturation_by_stage = {
        metric.stage_id: metric.value
        for metric in report.telemetry_metric_events
        if metric.metric_name == "retry_budget_saturation_ratio"
    }
    workflow_latency_ms = next(
        metric.value
        for metric in report.telemetry_metric_events
        if metric.metric_name == "orchestration_latency_ms"
    )

    return {
        "workflow_id": workflow_id,
        "status": "completed" if report.failed_stage is None and report.blocked_stage is None else "failed",
        "workflow_latency_ms": workflow_latency_ms,
        "stage_latency_by_stage": stage_latency_by_stage,
        "retry_saturation_by_stage": retry_saturation_by_stage,
    }


def _summarize_stage_profiles(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stage_ids = sorted(reports[0]["stage_latency_by_stage"].keys())
    summary: list[dict[str, Any]] = []
    for stage_id in stage_ids:
        latencies = [run["stage_latency_by_stage"][stage_id] for run in reports]
        saturations = [run["retry_saturation_by_stage"][stage_id] for run in reports]
        summary.append(
            {
                "stage_id": stage_id,
                "avg_stage_latency_ms": round(mean(latencies), 3),
                "p95_stage_latency_ms": _percentile(sorted(latencies), 0.95),
                "avg_retry_saturation_ratio": round(mean(saturations), 4),
            }
        )
    return summary


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    index = int(round((len(sorted_values) - 1) * percentile))
    index = max(0, min(index, len(sorted_values) - 1))
    return float(sorted_values[index])


def _mitigation_for_stage(stage_id: str) -> str:
    if stage_id == "artifact_export":
        return "Pre-render templates and batch checksum operations to reduce retry pressure on export paths."
    if stage_id == "compliance_review":
        return "Queue approvals by role and pre-validate gate payloads to shorten decision latency."
    return "Increase worker pool cautiously and preserve retry-budget alerts for this stage."
