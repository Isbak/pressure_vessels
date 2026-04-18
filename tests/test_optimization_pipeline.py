import json
from datetime import datetime, timezone

import pytest

from pressure_vessels.optimization_pipeline import (
    CANDIDATE_RANKING_REPORT_VERSION,
    OPTIMIZATION_SERVICE_VERSION,
    OptimizationCandidate,
    OptimizationWeights,
    run_optimization_service,
    write_optimization_artifacts,
)

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _candidates() -> list[OptimizationCandidate]:
    return [
        OptimizationCandidate(
            candidate_id="C-001",
            shell_thickness_m=0.017,
            head_thickness_m=0.016,
            nozzle_thickness_m=0.006,
            dry_weight_kg=9800.0,
            estimated_cost_usd=80500.0,
            manufacturability_score=0.88,
            hard_compliance_pass=True,
            compliance_justification="All mandatory UG-27/UG-32/UG-45 and route checks pass.",
        ),
        OptimizationCandidate(
            candidate_id="C-002",
            shell_thickness_m=0.016,
            head_thickness_m=0.015,
            nozzle_thickness_m=0.005,
            dry_weight_kg=9300.0,
            estimated_cost_usd=84500.0,
            manufacturability_score=0.81,
            hard_compliance_pass=True,
            compliance_justification="All mandatory UG-27/UG-32/UG-45 and route checks pass.",
        ),
        OptimizationCandidate(
            candidate_id="C-003",
            shell_thickness_m=0.018,
            head_thickness_m=0.016,
            nozzle_thickness_m=0.006,
            dry_weight_kg=10050.0,
            estimated_cost_usd=78000.0,
            manufacturability_score=0.73,
            hard_compliance_pass=True,
            compliance_justification="All mandatory UG-27/UG-32/UG-45 and route checks pass.",
        ),
        OptimizationCandidate(
            candidate_id="C-004",
            shell_thickness_m=0.015,
            head_thickness_m=0.014,
            nozzle_thickness_m=0.005,
            dry_weight_kg=9000.0,
            estimated_cost_usd=77000.0,
            manufacturability_score=0.92,
            hard_compliance_pass=False,
            compliance_justification="Rejected: UG-32 head MAWP below design pressure.",
        ),
    ]


def test_objective_scoring_supports_deterministic_tradeoff_reweighting():
    candidates = _candidates()

    weight_optimized, _ = run_optimization_service(
        candidates,
        weights=OptimizationWeights(weight=0.70, cost=0.20, manufacturability=0.10),
        source_ref="BL-010:test",
        now_utc=FIXED_NOW,
    )
    cost_optimized, _ = run_optimization_service(
        candidates,
        weights=OptimizationWeights(weight=0.20, cost=0.70, manufacturability=0.10),
        source_ref="BL-010:test",
        now_utc=FIXED_NOW,
    )

    assert weight_optimized.schema_version == OPTIMIZATION_SERVICE_VERSION
    assert cost_optimized.schema_version == OPTIMIZATION_SERVICE_VERSION
    assert weight_optimized.ranked_candidates[0].candidate_id == "C-002"
    assert cost_optimized.ranked_candidates[0].candidate_id == "C-003"


def test_hard_compliance_gate_filters_outputs_and_pareto_set():
    artifact, report = run_optimization_service(
        _candidates(),
        source_ref="BL-010:test",
        now_utc=FIXED_NOW,
    )

    assert report.schema_version == CANDIDATE_RANKING_REPORT_VERSION
    assert all(candidate.hard_compliance_pass for candidate in artifact.compliant_candidates)
    assert all(row.candidate_id != "C-004" for row in artifact.ranked_candidates)
    assert "C-004" not in artifact.pareto_candidate_ids
    assert any(candidate.candidate_id == "C-004" for candidate in artifact.rejected_candidates)


def test_ranking_and_justification_metadata_are_deterministic(tmp_path):
    candidates = _candidates()
    first_artifact, first_report = run_optimization_service(
        candidates,
        source_ref="BL-010:test",
        now_utc=FIXED_NOW,
    )
    second_artifact, second_report = run_optimization_service(
        list(reversed(candidates)),
        source_ref="BL-010:test",
        now_utc=FIXED_NOW,
    )

    assert first_artifact.deterministic_hash == second_artifact.deterministic_hash
    assert first_report.deterministic_hash == second_report.deterministic_hash
    assert [row.candidate_id for row in first_artifact.ranked_candidates] == [
        row.candidate_id for row in second_artifact.ranked_candidates
    ]
    assert first_artifact.ranked_candidates[0].rationale

    service_path, report_path = write_optimization_artifacts(
        first_artifact,
        first_report,
        tmp_path,
        filename_prefix="sample",
    )

    with service_path.open(encoding="utf-8") as handle:
        on_disk_service = json.load(handle)
    with report_path.open(encoding="utf-8") as handle:
        on_disk_report = json.load(handle)

    assert on_disk_service == first_artifact.to_json_dict()
    assert on_disk_report == first_report.to_json_dict()


def test_raises_when_all_candidates_are_non_compliant():
    invalid = [
        OptimizationCandidate(
            candidate_id="C-404",
            shell_thickness_m=0.015,
            head_thickness_m=0.014,
            nozzle_thickness_m=0.005,
            dry_weight_kg=9000.0,
            estimated_cost_usd=77000.0,
            manufacturability_score=0.92,
            hard_compliance_pass=False,
            compliance_justification="Rejected for hard compliance.",
        )
    ]

    with pytest.raises(ValueError, match="no compliant candidates"):
        run_optimization_service(invalid, now_utc=FIXED_NOW)
