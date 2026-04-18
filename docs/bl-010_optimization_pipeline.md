# BL-010 Optimization Service (Cost + Manufacturability)

BL-010 introduces a deterministic optimization layer that ranks feasible vessel candidates while preserving hard compliance constraints.

## Scope

- Objective scoring supports trade-offs across:
  - `dry_weight_kg` (minimize)
  - `estimated_cost_usd` (minimize)
  - `manufacturability_score` (maximize)
- Hard compliance (`hard_compliance_pass`) is a strict gate.
- Pareto frontier candidates are exported with deterministic ranking and rationale metadata.

## API

Implemented in `src/pressure_vessels/optimization_pipeline.py`:

- `run_optimization_service(candidates, *, weights=None, source_ref="unspecified", now_utc=None)`
  - Returns:
    - `OptimizationServiceArtifact`
    - `CandidateRankingReport`
- `write_optimization_artifacts(optimization_artifact, ranking_report, directory, *, filename_prefix="")`
  - Writes canonical JSON outputs.

## Artifact Schemas

### `OptimizationService.v1`

- `schema_version`
- `generated_at_utc`
- `source_ref`
- `weights` (normalized internally to sum to `1.0`)
- `compliant_candidates`
- `rejected_candidates`
- `pareto_candidate_ids`
- `ranked_candidates`
  - includes normalized terms, objective values, Pareto status, and rationale list
- `deterministic_hash`

### `CandidateRankingReport.v1`

- `schema_version`
- `generated_at_utc`
- `source_optimization_hash`
- `summary_lines`
- `ranking_rows`
- `deterministic_hash`

## Determinism and Stability

- Candidate IDs must be unique and non-empty.
- Input order does not affect ranking output.
- Tie-breaking order is deterministic:
  1. composite score (descending)
  2. Pareto status (`true` before `false`)
  3. lower weight
  4. lower cost
  5. higher manufacturability
  6. candidate ID lexical order

## Compliance Guardrail

Only `hard_compliance_pass=true` candidates are eligible for scoring, Pareto frontier selection, and ranking.
Rejected candidates are preserved in the artifact metadata for auditability.
