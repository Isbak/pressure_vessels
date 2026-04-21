"""BL-017 QA benchmark dataset and deterministic cross-verification harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .calculation_pipeline import Quantity, SizingCheckInput, run_calculation_pipeline
from .design_basis_pipeline import build_design_basis
from .requirements_pipeline import parse_prompt_to_requirement_set

QA_BENCHMARK_DATASET_MANIFEST_VERSION = "QABenchmarkDatasetManifest.v1"
QA_QUALITY_GATE_REPORT_VERSION = "QABenchmarkQualityGateReport.v1"

DEFAULT_BENCHMARK_PROMPT = (
    "Design a horizontal pressure vessel for propane storage, "
    "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
    "ASME Section VIII Div 1, corrosion allowance 3 mm."
)


@dataclass(frozen=True)
class BenchmarkCaseManifestEntry:
    case_id: str
    fixture_path: str
    category: str
    description: str


@dataclass(frozen=True)
class BenchmarkDatasetManifest:
    schema_version: str
    manifest_id: str
    deterministic_timestamp_utc: str
    benchmark_prompt: str
    cases: tuple[BenchmarkCaseManifestEntry, ...]


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def load_benchmark_dataset_manifest(manifest_path: Path) -> BenchmarkDatasetManifest:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = tuple(
        BenchmarkCaseManifestEntry(
            case_id=entry["case_id"],
            fixture_path=entry["fixture_path"],
            category=entry["category"],
            description=entry["description"],
        )
        for entry in payload["cases"]
    )
    return BenchmarkDatasetManifest(
        schema_version=payload["schema_version"],
        manifest_id=payload["manifest_id"],
        deterministic_timestamp_utc=payload["deterministic_timestamp_utc"],
        benchmark_prompt=payload.get("benchmark_prompt", DEFAULT_BENCHMARK_PROMPT),
        cases=entries,
    )


def run_cross_verification_harness(
    manifest: BenchmarkDatasetManifest,
    *,
    manifest_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    now_utc = datetime.fromisoformat(manifest.deterministic_timestamp_utc.replace("Z", "+00:00"))

    requirement_set = parse_prompt_to_requirement_set(manifest.benchmark_prompt, now_utc=now_utc)
    design_basis, applicability_matrix = build_design_basis(requirement_set, now_utc=now_utc)

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_sha256 = _sha256(manifest_payload)

    case_results: list[dict[str, Any]] = []
    total_failures = 0

    baseline_sizing_input = SizingCheckInput(
        internal_pressure=Quantity(value=1_600_000.0, unit="Pa"),
        allowable_stress=Quantity(value=150_000_000.0, unit="Pa"),
        joint_efficiency=0.9,
        corrosion_allowance=Quantity(value=0.002, unit="m"),
        shell_inside_diameter=Quantity(value=1.8, unit="m"),
        shell_provided_thickness=Quantity(value=0.016, unit="m"),
        head_inside_diameter=Quantity(value=1.8, unit="m"),
        head_provided_thickness=Quantity(value=0.014, unit="m"),
        nozzle_inside_diameter=Quantity(value=0.25, unit="m"),
        nozzle_provided_thickness=Quantity(value=0.006, unit="m"),
    )

    for case in manifest.cases:
        fixture_path = repo_root / case.fixture_path
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        check_results: list[dict[str, Any]] = []
        if case.category == "reject":
            for reject_case in fixture["cases"]:
                sizing_input = SizingCheckInput(
                    internal_pressure=Quantity(
                        value=reject_case["value"]
                        if reject_case["dimension"] == "internal_pressure_pa"
                        else baseline_sizing_input.internal_pressure.value,
                        unit="Pa",
                    ),
                    allowable_stress=Quantity(
                        value=reject_case["value"]
                        if reject_case["dimension"] == "allowable_stress_pa"
                        else baseline_sizing_input.allowable_stress.value,
                        unit="Pa",
                    ),
                    joint_efficiency=reject_case["value"]
                    if reject_case["dimension"] == "joint_efficiency"
                    else baseline_sizing_input.joint_efficiency,
                    corrosion_allowance=Quantity(
                        value=reject_case["value"]
                        if reject_case["dimension"] == "corrosion_allowance_m"
                        else baseline_sizing_input.corrosion_allowance.value,
                        unit="m",
                    ),
                    shell_inside_diameter=baseline_sizing_input.shell_inside_diameter,
                    shell_provided_thickness=baseline_sizing_input.shell_provided_thickness,
                    head_inside_diameter=baseline_sizing_input.head_inside_diameter,
                    head_provided_thickness=baseline_sizing_input.head_provided_thickness,
                    nozzle_inside_diameter=Quantity(
                        value=reject_case["value"]
                        if reject_case["dimension"] == "nozzle_inside_diameter_m"
                        else baseline_sizing_input.nozzle_inside_diameter.value,
                        unit="m",
                    ),
                    nozzle_provided_thickness=baseline_sizing_input.nozzle_provided_thickness,
                )

                matched = False
                observed_error = ""
                try:
                    run_calculation_pipeline(
                        requirement_set,
                        design_basis,
                        applicability_matrix,
                        sizing_input=sizing_input,
                        now_utc=now_utc,
                    )
                except ValueError as exc:
                    observed_error = str(exc)
                    matched = re.search(reject_case["expected_error_regex"], observed_error) is not None

                if not matched:
                    total_failures += 1

                check_results.append(
                    {
                        "check_id": reject_case["case_id"],
                        "matched": matched,
                        "dimension": reject_case["dimension"],
                        "value": reject_case["value"],
                        "expected_error_regex": reject_case["expected_error_regex"],
                        "observed_error": observed_error,
                    }
                )
        else:
            fixture_input = fixture["input"]
            sizing_input = SizingCheckInput(
                internal_pressure=Quantity(value=fixture_input["internal_pressure_pa"], unit="Pa"),
                allowable_stress=Quantity(value=fixture_input["allowable_stress_pa"], unit="Pa"),
                joint_efficiency=fixture_input["joint_efficiency"],
                corrosion_allowance=Quantity(value=fixture_input["corrosion_allowance_m"], unit="m"),
                shell_inside_diameter=Quantity(value=fixture_input["shell_inside_diameter_m"], unit="m"),
                shell_provided_thickness=Quantity(value=fixture_input["shell_provided_thickness_m"], unit="m"),
                head_inside_diameter=Quantity(value=fixture_input["head_inside_diameter_m"], unit="m"),
                head_provided_thickness=Quantity(value=fixture_input["head_provided_thickness_m"], unit="m"),
                nozzle_inside_diameter=Quantity(value=fixture_input["nozzle_inside_diameter_m"], unit="m"),
                nozzle_provided_thickness=Quantity(value=fixture_input["nozzle_provided_thickness_m"], unit="m"),
            )
            calculation_artifact, _ = run_calculation_pipeline(
                requirement_set,
                design_basis,
                applicability_matrix,
                sizing_input=sizing_input,
                now_utc=now_utc,
            )
            checks_by_id = {record.check_id: record for record in calculation_artifact.checks}
            tolerance = fixture["tolerance"]
            for check_id, expected in fixture["expected"].items():
                actual = checks_by_id[check_id]
                pass_matches = actual.pass_status is expected["pass_status"]
                thickness_matches = True
                mawp_matches = True
                if "required_thickness_m" in expected:
                    thickness_matches = abs(actual.required_thickness_m - expected["required_thickness_m"]) <= tolerance
                if "computed_mawp_pa" in expected:
                    mawp_matches = abs((actual.computed_mawp_pa or 0.0) - expected["computed_mawp_pa"]) <= tolerance
                matched = pass_matches and thickness_matches and mawp_matches
                if not matched:
                    total_failures += 1
                check_results.append(
                    {
                        "check_id": check_id,
                        "matched": matched,
                        "pass_status_expected": expected["pass_status"],
                        "pass_status_actual": actual.pass_status,
                        "required_thickness_expected_m": expected.get("required_thickness_m"),
                        "required_thickness_actual_m": actual.required_thickness_m,
                        "computed_mawp_expected_pa": expected.get("computed_mawp_pa"),
                        "computed_mawp_actual_pa": actual.computed_mawp_pa,
                    }
                )
            calculation_hash = calculation_artifact.deterministic_hash

        case_status = "pass" if all(result["matched"] for result in check_results) else "fail"
        case_payload = {
            "case_id": case.case_id,
            "fixture_id": fixture["id"],
            "fixture_path": case.fixture_path,
            "category": case.category,
            "description": case.description,
            "status": case_status,
            "calculation_hash": calculation_hash if case.category != "reject" else None,
            "check_results": check_results,
        }
        case_results.append({**case_payload, "deterministic_hash": _sha256(case_payload)})

    summary = {
        "total_cases": len(case_results),
        "pass_cases": sum(1 for case in case_results if case["status"] == "pass"),
        "fail_cases": sum(1 for case in case_results if case["status"] == "fail"),
        "total_check_failures": total_failures,
    }
    report_body = {
        "schema_version": QA_QUALITY_GATE_REPORT_VERSION,
        "manifest": {
            "manifest_id": manifest.manifest_id,
            "manifest_path": str(manifest_path.as_posix()),
            "manifest_sha256": manifest_sha256,
            "schema_version": manifest.schema_version,
        },
        "summary": summary,
        "overall_status": "pass" if summary["fail_cases"] == 0 else "fail",
        "case_results": case_results,
    }
    return {**report_body, "deterministic_hash": _sha256(report_body)}


def write_quality_gate_report(report: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
