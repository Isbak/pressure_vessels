"""Deterministic optimization service for BL-010."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

OPTIMIZATION_SERVICE_VERSION = "OptimizationService.v1"
CANDIDATE_RANKING_REPORT_VERSION = "CandidateRankingReport.v1"


@dataclass(frozen=True)
class OptimizationWeights:
    weight: float
    cost: float
    manufacturability: float

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OptimizationCandidate:
    candidate_id: str
    shell_thickness_m: float
    head_thickness_m: float
    nozzle_thickness_m: float
    dry_weight_kg: float
    estimated_cost_usd: float
    manufacturability_score: float
    hard_compliance_pass: bool
    compliance_justification: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RankedCandidate:
    rank: int
    candidate_id: str
    composite_score: float
    normalized_terms: dict[str, float]
    objective_values: dict[str, float]
    pareto_optimal: bool
    rationale: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "candidate_id": self.candidate_id,
            "composite_score": self.composite_score,
            "normalized_terms": self.normalized_terms,
            "objective_values": self.objective_values,
            "pareto_optimal": self.pareto_optimal,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class OptimizationServiceArtifact:
    schema_version: str
    generated_at_utc: str
    source_ref: str
    weights: OptimizationWeights
    compliant_candidates: list[OptimizationCandidate]
    rejected_candidates: list[OptimizationCandidate]
    pareto_candidate_ids: list[str]
    ranked_candidates: list[RankedCandidate]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_ref": self.source_ref,
            "weights": self.weights.to_json_dict(),
            "compliant_candidates": [candidate.to_json_dict() for candidate in self.compliant_candidates],
            "rejected_candidates": [candidate.to_json_dict() for candidate in self.rejected_candidates],
            "pareto_candidate_ids": self.pareto_candidate_ids,
            "ranked_candidates": [candidate.to_json_dict() for candidate in self.ranked_candidates],
            "deterministic_hash": self.deterministic_hash,
        }


@dataclass(frozen=True)
class CandidateRankingReport:
    schema_version: str
    generated_at_utc: str
    source_optimization_hash: str
    summary_lines: list[str]
    ranking_rows: list[dict[str, Any]]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_optimization_hash": self.source_optimization_hash,
            "summary_lines": self.summary_lines,
            "ranking_rows": self.ranking_rows,
            "deterministic_hash": self.deterministic_hash,
        }


def run_optimization_service(
    candidates: list[OptimizationCandidate],
    *,
    weights: OptimizationWeights | None = None,
    source_ref: str = "unspecified",
    now_utc: datetime | None = None,
) -> tuple[OptimizationServiceArtifact, CandidateRankingReport]:
    """Rank feasible candidates by deterministic weight/cost/manufacturability trade-off scoring."""
    _validate_candidates(candidates)
    active_weights = _validate_weights(weights or OptimizationWeights(weight=0.4, cost=0.4, manufacturability=0.2))

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    compliant = sorted((candidate for candidate in candidates if candidate.hard_compliance_pass), key=lambda c: c.candidate_id)
    rejected = sorted((candidate for candidate in candidates if not candidate.hard_compliance_pass), key=lambda c: c.candidate_id)
    if not compliant:
        raise ValueError("BL-010 optimization failed: no compliant candidates available for ranking.")

    pareto_ids = _pareto_candidate_ids(compliant)
    ranked = _rank_candidates(compliant, active_weights, pareto_ids)

    artifact_payload = {
        "schema_version": OPTIMIZATION_SERVICE_VERSION,
        "generated_at_utc": generated_at,
        "source_ref": source_ref,
        "weights": active_weights.to_json_dict(),
        "compliant_candidates": [candidate.to_json_dict() for candidate in compliant],
        "rejected_candidates": [candidate.to_json_dict() for candidate in rejected],
        "pareto_candidate_ids": pareto_ids,
        "ranked_candidates": [candidate.to_json_dict() for candidate in ranked],
    }
    artifact_hash = _sha256_payload(artifact_payload)
    artifact = OptimizationServiceArtifact(
        schema_version=OPTIMIZATION_SERVICE_VERSION,
        generated_at_utc=generated_at,
        source_ref=source_ref,
        weights=active_weights,
        compliant_candidates=compliant,
        rejected_candidates=rejected,
        pareto_candidate_ids=pareto_ids,
        ranked_candidates=ranked,
        deterministic_hash=artifact_hash,
    )

    report_payload = {
        "schema_version": CANDIDATE_RANKING_REPORT_VERSION,
        "generated_at_utc": generated_at,
        "source_optimization_hash": artifact_hash,
        "summary_lines": [
            f"Compliant candidates ranked: {len(ranked)}",
            f"Rejected for hard compliance: {len(rejected)}",
            f"Pareto candidate count: {len(pareto_ids)}",
            (
                "Objective weights: "
                f"weight={active_weights.weight:.3f}, "
                f"cost={active_weights.cost:.3f}, "
                f"manufacturability={active_weights.manufacturability:.3f}"
            ),
        ],
        "ranking_rows": [
            {
                "rank": row.rank,
                "candidate_id": row.candidate_id,
                "composite_score": row.composite_score,
                "pareto_optimal": row.pareto_optimal,
                "rationale": "; ".join(row.rationale),
            }
            for row in ranked
        ],
    }
    report_hash = _sha256_payload(report_payload)

    report = CandidateRankingReport(
        schema_version=CANDIDATE_RANKING_REPORT_VERSION,
        generated_at_utc=generated_at,
        source_optimization_hash=artifact_hash,
        summary_lines=report_payload["summary_lines"],
        ranking_rows=report_payload["ranking_rows"],
        deterministic_hash=report_hash,
    )

    return artifact, report


def write_optimization_artifacts(
    optimization_artifact: OptimizationServiceArtifact,
    ranking_report: CandidateRankingReport,
    directory: str | Path,
    *,
    filename_prefix: str = "",
) -> tuple[Path, Path]:
    """Persist optimization service and ranking report artifacts in canonical JSON form."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)

    prefix = filename_prefix.strip()
    if prefix and not prefix.endswith("."):
        prefix = f"{prefix}."

    optimization_path = target / f"{prefix}OptimizationService.v1.json"
    ranking_path = target / f"{prefix}CandidateRankingReport.v1.json"

    _write_json(optimization_path, optimization_artifact.to_json_dict())
    _write_json(ranking_path, ranking_report.to_json_dict())

    return optimization_path, ranking_path


def _validate_candidates(candidates: list[OptimizationCandidate]) -> None:
    if not candidates:
        raise ValueError("BL-010 optimization failed: at least one candidate is required.")

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate.candidate_id.strip():
            raise ValueError("BL-010 optimization failed: candidate_id must be non-empty.")
        if candidate.candidate_id in seen:
            raise ValueError(f"BL-010 optimization failed: duplicate candidate_id '{candidate.candidate_id}'.")
        seen.add(candidate.candidate_id)
        if candidate.dry_weight_kg <= 0 or candidate.estimated_cost_usd <= 0:
            raise ValueError("BL-010 optimization failed: weight and cost must be positive.")
        if not 0.0 <= candidate.manufacturability_score <= 1.0:
            raise ValueError(
                "BL-010 optimization failed: manufacturability_score must be within [0.0, 1.0]."
            )


def _validate_weights(weights: OptimizationWeights) -> OptimizationWeights:
    if weights.weight < 0 or weights.cost < 0 or weights.manufacturability < 0:
        raise ValueError("BL-010 optimization failed: objective weights must be non-negative.")
    total = weights.weight + weights.cost + weights.manufacturability
    if total <= 0:
        raise ValueError("BL-010 optimization failed: objective weight sum must be > 0.")
    return OptimizationWeights(
        weight=weights.weight / total,
        cost=weights.cost / total,
        manufacturability=weights.manufacturability / total,
    )


def _pareto_candidate_ids(candidates: list[OptimizationCandidate]) -> list[str]:
    pareto: list[str] = []
    for candidate in candidates:
        dominated = False
        for other in candidates:
            if other.candidate_id == candidate.candidate_id:
                continue
            better_or_equal = (
                other.dry_weight_kg <= candidate.dry_weight_kg
                and other.estimated_cost_usd <= candidate.estimated_cost_usd
                and other.manufacturability_score >= candidate.manufacturability_score
            )
            strictly_better = (
                other.dry_weight_kg < candidate.dry_weight_kg
                or other.estimated_cost_usd < candidate.estimated_cost_usd
                or other.manufacturability_score > candidate.manufacturability_score
            )
            if better_or_equal and strictly_better:
                dominated = True
                break
        if not dominated:
            pareto.append(candidate.candidate_id)
    return sorted(pareto)


def _rank_candidates(
    compliant: list[OptimizationCandidate],
    weights: OptimizationWeights,
    pareto_ids: list[str],
) -> list[RankedCandidate]:
    min_weight = min(candidate.dry_weight_kg for candidate in compliant)
    max_weight = max(candidate.dry_weight_kg for candidate in compliant)
    min_cost = min(candidate.estimated_cost_usd for candidate in compliant)
    max_cost = max(candidate.estimated_cost_usd for candidate in compliant)

    scored: list[RankedCandidate] = []
    for candidate in compliant:
        weight_score = 1.0 - _minimize_normalized(candidate.dry_weight_kg, min_weight, max_weight)
        cost_score = 1.0 - _minimize_normalized(candidate.estimated_cost_usd, min_cost, max_cost)
        manufacturability_score = candidate.manufacturability_score

        composite = (
            weights.weight * weight_score
            + weights.cost * cost_score
            + weights.manufacturability * manufacturability_score
        )

        rationale = [
            "Hard compliance gate passed.",
            (
                "Weighted objective contributions: "
                f"weight={weights.weight * weight_score:.6f}, "
                f"cost={weights.cost * cost_score:.6f}, "
                f"manufacturability={weights.manufacturability * manufacturability_score:.6f}"
            ),
            f"Pareto frontier status: {'on_frontier' if candidate.candidate_id in pareto_ids else 'dominated'}.",
            candidate.compliance_justification,
        ]

        scored.append(
            RankedCandidate(
                rank=0,
                candidate_id=candidate.candidate_id,
                composite_score=round(composite, 9),
                normalized_terms={
                    "weight_benefit": round(weight_score, 9),
                    "cost_benefit": round(cost_score, 9),
                    "manufacturability": round(manufacturability_score, 9),
                },
                objective_values={
                    "dry_weight_kg": candidate.dry_weight_kg,
                    "estimated_cost_usd": candidate.estimated_cost_usd,
                    "manufacturability_score": candidate.manufacturability_score,
                },
                pareto_optimal=candidate.candidate_id in pareto_ids,
                rationale=rationale,
            )
        )

    ordered = sorted(
        scored,
        key=lambda row: (
            -row.composite_score,
            -int(row.pareto_optimal),
            row.objective_values["dry_weight_kg"],
            row.objective_values["estimated_cost_usd"],
            -row.objective_values["manufacturability_score"],
            row.candidate_id,
        ),
    )

    ranked: list[RankedCandidate] = []
    for index, row in enumerate(ordered, start=1):
        ranked.append(
            RankedCandidate(
                rank=index,
                candidate_id=row.candidate_id,
                composite_score=row.composite_score,
                normalized_terms=row.normalized_terms,
                objective_values=row.objective_values,
                pareto_optimal=row.pareto_optimal,
                rationale=row.rationale,
            )
        )
    return ranked


def _minimize_normalized(value: float, minimum: float, maximum: float) -> float:
    if maximum == minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
