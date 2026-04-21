"""Deterministic standards ingestion pipeline for BL-005."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

STANDARDS_PACKAGE_VERSION = "StandardsPackage.v1"
LIFECYCLE_STAGES = ("draft", "candidate", "released")
LIFECYCLE_APPROVAL_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "draft": tuple(),
    "candidate": ("engineering_reviewer",),
    "released": ("engineering_reviewer", "domain_reviewer"),
}


@dataclass(frozen=True)
class StandardSource:
    source_id: str
    title: str
    publisher: str
    edition: str
    revision: str
    content_text: str


@dataclass(frozen=True)
class ParsedClause:
    clause_id: str
    text: str
    equation: str | None
    cross_references: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedClause:
    clause_id: str
    canonical_text: str
    canonical_equation: str | None
    canonical_variables: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticLink:
    from_clause_id: str
    to_clause_id: str
    link_type: str
    reason: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RegressionExample:
    example_id: str
    required_clause_ids: list[str]
    required_link_pairs: list[tuple[str, str]]


@dataclass(frozen=True)
class RegressionResult:
    example_id: str
    passed: bool
    details: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalRecord:
    role: str
    approver_id: str
    approved_at_utc: str
    decision: str = "approved"

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LifecycleState:
    stage: str
    promoted_at_utc: str
    promoted_by: str
    approvals: list[ApprovalRecord]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "promoted_at_utc": self.promoted_at_utc,
            "promoted_by": self.promoted_by,
            "approvals": [approval.to_json_dict() for approval in self.approvals],
        }


@dataclass(frozen=True)
class CrossVersionRegressionCase:
    case_id: str
    clause_id: str
    metric: str
    baseline_value: str
    candidate_value: str
    passed: bool
    details: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CrossVersionRegressionReport:
    baseline_package_id: str
    candidate_package_id: str
    generated_at_utc: str
    drift_detected: bool
    cases: list[CrossVersionRegressionCase]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "baseline_package_id": self.baseline_package_id,
            "candidate_package_id": self.candidate_package_id,
            "generated_at_utc": self.generated_at_utc,
            "drift_detected": self.drift_detected,
            "cases": [case.to_json_dict() for case in self.cases],
        }


@dataclass(frozen=True)
class ProjectClauseDependency:
    project_id: str
    referenced_clause_ids: list[str]


@dataclass(frozen=True)
class VersionImpactReport:
    baseline_package_id: str
    candidate_package_id: str
    generated_at_utc: str
    changed_clause_ids: list[str]
    affected_projects: list[str]
    selective_reverification_scope: dict[str, list[str]]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "baseline_package_id": self.baseline_package_id,
            "candidate_package_id": self.candidate_package_id,
            "generated_at_utc": self.generated_at_utc,
            "changed_clause_ids": self.changed_clause_ids,
            "affected_projects": self.affected_projects,
            "selective_reverification_scope": self.selective_reverification_scope,
        }


@dataclass(frozen=True)
class StandardsPackage:
    schema_version: str
    generated_at_utc: str
    standard_key: str
    standard_version: str
    release_label: str
    immutable: bool
    source_fingerprints: list[dict[str, str]]
    parsed_clauses: list[ParsedClause]
    normalized_clauses: list[NormalizedClause]
    semantic_links: list[SemanticLink]
    regression_results: list[RegressionResult]
    lifecycle: LifecycleState
    cross_version_regression: CrossVersionRegressionReport | None
    impact_analysis: VersionImpactReport | None
    deterministic_hash: str

    @property
    def package_id(self) -> str:
        return f"{self.standard_key}_{self.standard_version}_{self.release_label}"

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "package_id": self.package_id,
            "standard_key": self.standard_key,
            "standard_version": self.standard_version,
            "release_label": self.release_label,
            "immutable": self.immutable,
            "source_fingerprints": self.source_fingerprints,
            "parsed_clauses": [clause.to_json_dict() for clause in self.parsed_clauses],
            "normalized_clauses": [clause.to_json_dict() for clause in self.normalized_clauses],
            "semantic_links": [link.to_json_dict() for link in self.semantic_links],
            "regression_results": [result.to_json_dict() for result in self.regression_results],
            "lifecycle": self.lifecycle.to_json_dict(),
            "cross_version_regression": (
                self.cross_version_regression.to_json_dict() if self.cross_version_regression else None
            ),
            "impact_analysis": self.impact_analysis.to_json_dict() if self.impact_analysis else None,
            "deterministic_hash": self.deterministic_hash,
        }


class StandardsPackageCollisionError(FileExistsError):
    """Raised when a standards package path already exists or is being published."""


def run_standards_ingestion(
    *,
    source_documents: list[StandardSource],
    standard_key: str,
    standard_version: str,
    release_label: str,
    regression_examples: list[RegressionExample],
    lifecycle_stage: str = "draft",
    promoted_by: str = "system",
    approvals: list[ApprovalRecord] | None = None,
    baseline_package: StandardsPackage | None = None,
    project_clause_dependencies: list[ProjectClauseDependency] | None = None,
    now_utc: datetime | None = None,
) -> StandardsPackage:
    """Run source intake, parse, normalize, semantic link, validate, and release packaging."""
    _validate_source_intake(source_documents)
    _validate_release_metadata(standard_key, standard_version, release_label)

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    parsed_clauses = _parse_sources(source_documents)
    normalized_clauses = _normalize_clauses(parsed_clauses)
    semantic_links = _build_semantic_links(parsed_clauses)
    _validate_artifact_consistency(parsed_clauses, normalized_clauses, semantic_links)

    regression_results = _run_regression_examples(
        regression_examples=regression_examples,
        parsed_clauses=parsed_clauses,
        semantic_links=semantic_links,
    )
    failures = [result for result in regression_results if not result.passed]
    if failures:
        failed_ids = ", ".join(result.example_id for result in failures)
        raise ValueError(f"BL-005 release gate failed: regression examples failed ({failed_ids}).")

    source_fingerprints = _build_source_fingerprints(source_documents)
    lifecycle = _build_lifecycle_state(
        stage=lifecycle_stage,
        promoted_by=promoted_by,
        approvals=approvals or [],
        promoted_at_utc=generated_at,
    )
    cross_version_regression = (
        run_cross_version_regression(
            baseline_package=baseline_package,
            candidate_package_metadata={
                "package_id": f"{standard_key}_{standard_version}_{release_label}",
                "normalized_clauses": normalized_clauses,
                "semantic_links": semantic_links,
            },
            generated_at_utc=generated_at,
        )
        if baseline_package
        else None
    )
    if lifecycle.stage == "released" and cross_version_regression and cross_version_regression.drift_detected:
        raise ValueError("BL-036 release gate failed: cross-version regression detected drift.")
    impact_analysis = (
        generate_version_impact_report(
            baseline_package=baseline_package,
            candidate_package_metadata={
                "package_id": f"{standard_key}_{standard_version}_{release_label}",
                "normalized_clauses": normalized_clauses,
            },
            project_clause_dependencies=project_clause_dependencies or [],
            generated_at_utc=generated_at,
        )
        if baseline_package
        else None
    )
    unsigned_payload = {
        "schema_version": STANDARDS_PACKAGE_VERSION,
        "generated_at_utc": generated_at,
        "standard_key": standard_key,
        "standard_version": standard_version,
        "release_label": release_label,
        "immutable": True,
        "source_fingerprints": source_fingerprints,
        "parsed_clauses": [clause.to_json_dict() for clause in parsed_clauses],
        "normalized_clauses": [clause.to_json_dict() for clause in normalized_clauses],
        "semantic_links": [link.to_json_dict() for link in semantic_links],
        "regression_results": [result.to_json_dict() for result in regression_results],
        "lifecycle": lifecycle.to_json_dict(),
        "cross_version_regression": (
            cross_version_regression.to_json_dict() if cross_version_regression else None
        ),
        "impact_analysis": impact_analysis.to_json_dict() if impact_analysis else None,
    }
    deterministic_hash = _sha256_payload(unsigned_payload)

    return StandardsPackage(
        schema_version=STANDARDS_PACKAGE_VERSION,
        generated_at_utc=generated_at,
        standard_key=standard_key,
        standard_version=standard_version,
        release_label=release_label,
        immutable=True,
        source_fingerprints=source_fingerprints,
        parsed_clauses=parsed_clauses,
        normalized_clauses=normalized_clauses,
        semantic_links=semantic_links,
        regression_results=regression_results,
        lifecycle=lifecycle,
        cross_version_regression=cross_version_regression,
        impact_analysis=impact_analysis,
        deterministic_hash=deterministic_hash,
    )


def promote_standards_package(
    package: StandardsPackage,
    *,
    target_stage: str,
    promoted_by: str,
    approvals: list[ApprovalRecord],
    now_utc: datetime | None = None,
) -> StandardsPackage:
    """Promote package lifecycle from draft -> candidate -> released with approval checks."""
    _validate_lifecycle_stage(target_stage)
    current_index = LIFECYCLE_STAGES.index(package.lifecycle.stage)
    target_index = LIFECYCLE_STAGES.index(target_stage)
    if target_index != current_index + 1:
        raise ValueError(
            "BL-036 lifecycle control failed: transitions must be sequential "
            "(draft -> candidate -> released)."
        )
    promoted_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    lifecycle = _build_lifecycle_state(
        stage=target_stage,
        promoted_by=promoted_by,
        approvals=approvals,
        promoted_at_utc=promoted_at,
    )
    unsigned_payload = {
        "schema_version": package.schema_version,
        "generated_at_utc": package.generated_at_utc,
        "standard_key": package.standard_key,
        "standard_version": package.standard_version,
        "release_label": package.release_label,
        "immutable": package.immutable,
        "source_fingerprints": package.source_fingerprints,
        "parsed_clauses": [clause.to_json_dict() for clause in package.parsed_clauses],
        "normalized_clauses": [clause.to_json_dict() for clause in package.normalized_clauses],
        "semantic_links": [link.to_json_dict() for link in package.semantic_links],
        "regression_results": [result.to_json_dict() for result in package.regression_results],
        "lifecycle": lifecycle.to_json_dict(),
        "cross_version_regression": (
            package.cross_version_regression.to_json_dict() if package.cross_version_regression else None
        ),
        "impact_analysis": package.impact_analysis.to_json_dict() if package.impact_analysis else None,
    }
    return StandardsPackage(
        schema_version=package.schema_version,
        generated_at_utc=package.generated_at_utc,
        standard_key=package.standard_key,
        standard_version=package.standard_version,
        release_label=package.release_label,
        immutable=package.immutable,
        source_fingerprints=package.source_fingerprints,
        parsed_clauses=package.parsed_clauses,
        normalized_clauses=package.normalized_clauses,
        semantic_links=package.semantic_links,
        regression_results=package.regression_results,
        lifecycle=lifecycle,
        cross_version_regression=package.cross_version_regression,
        impact_analysis=package.impact_analysis,
        deterministic_hash=_sha256_payload(unsigned_payload),
    )


def write_standards_package(package: StandardsPackage, directory: str | Path) -> Path:
    """Persist an immutable standards package; fail if package ID already exists."""
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{package.package_id}.json"
    payload = json.dumps(package.to_json_dict(), indent=2, sort_keys=True)
    _atomic_write_json(output_path=output_path, package_id=package.package_id, payload=payload)
    return output_path


def _atomic_write_json(*, output_path: Path, package_id: str, payload: str) -> None:
    lock_path = Path(f"{output_path}.lock")
    temp_path = Path(f"{output_path}.tmp.{uuid4().hex}")
    lock_fd: int | None = None
    try:
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise StandardsPackageCollisionError(
                f"Standards package collision for package_id={package_id} at {output_path}."
            ) from exc

        if output_path.exists():
            raise StandardsPackageCollisionError(
                f"Standards package collision for package_id={package_id} at {output_path}."
            )

        with temp_path.open("x", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp_path, output_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if lock_path.exists():
            lock_path.unlink()


def _validate_source_intake(source_documents: list[StandardSource]) -> None:
    if not source_documents:
        raise ValueError("BL-005 source intake failed: at least one source document is required.")

    for source in source_documents:
        if not source.source_id.strip():
            raise ValueError("BL-005 source intake failed: source_id must be non-empty.")
        if not source.title.strip():
            raise ValueError(f"BL-005 source intake failed: title missing for source {source.source_id}.")
        if not source.publisher.strip() or not source.edition.strip() or not source.revision.strip():
            raise ValueError(
                f"BL-005 source intake failed: publisher/edition/revision missing for source {source.source_id}."
            )
        if not source.content_text.strip():
            raise ValueError(f"BL-005 source intake failed: content missing for source {source.source_id}.")


def _validate_release_metadata(standard_key: str, standard_version: str, release_label: str) -> None:
    if not standard_key.strip() or not standard_version.strip() or not release_label.strip():
        raise ValueError("BL-005 release gate failed: standard_key/version/release_label must be non-empty.")


def _validate_lifecycle_stage(stage: str) -> None:
    if stage not in LIFECYCLE_STAGES:
        valid = ", ".join(LIFECYCLE_STAGES)
        raise ValueError(f"BL-036 lifecycle control failed: stage must be one of [{valid}].")


def _build_lifecycle_state(
    *, stage: str, promoted_by: str, approvals: list[ApprovalRecord], promoted_at_utc: str
) -> LifecycleState:
    _validate_lifecycle_stage(stage)
    if not promoted_by.strip():
        raise ValueError("BL-036 lifecycle control failed: promoted_by must be non-empty.")
    required_roles = set(LIFECYCLE_APPROVAL_REQUIREMENTS[stage])
    approved_roles = {approval.role for approval in approvals if approval.decision == "approved"}
    missing_roles = sorted(required_roles - approved_roles)
    if missing_roles:
        raise ValueError(
            "BL-036 lifecycle control failed: missing required approvals "
            f"for stage {stage}: {', '.join(missing_roles)}."
        )
    ordered_approvals = sorted(approvals, key=lambda approval: (approval.role, approval.approver_id))
    return LifecycleState(
        stage=stage,
        promoted_at_utc=promoted_at_utc,
        promoted_by=promoted_by,
        approvals=ordered_approvals,
    )


def run_cross_version_regression(
    *,
    baseline_package: StandardsPackage,
    candidate_package_metadata: dict[str, Any],
    generated_at_utc: str,
) -> CrossVersionRegressionReport:
    """Compare baseline and candidate clause/link semantics and detect drift deterministically."""
    baseline_clauses = {
        clause.clause_id: (clause.canonical_text, clause.canonical_equation)
        for clause in baseline_package.normalized_clauses
    }
    candidate_clauses = {
        clause.clause_id: (clause.canonical_text, clause.canonical_equation)
        for clause in candidate_package_metadata["normalized_clauses"]
    }
    cases: list[CrossVersionRegressionCase] = []

    shared_clause_ids = sorted(set(baseline_clauses).intersection(candidate_clauses))
    for clause_id in shared_clause_ids:
        baseline_value = f"{baseline_clauses[clause_id][0]}|{baseline_clauses[clause_id][1]}"
        candidate_value = f"{candidate_clauses[clause_id][0]}|{candidate_clauses[clause_id][1]}"
        passed = baseline_value == candidate_value
        cases.append(
            CrossVersionRegressionCase(
                case_id=f"CLAUSE-{clause_id}",
                clause_id=clause_id,
                metric="normalized_clause_signature",
                baseline_value=baseline_value,
                candidate_value=candidate_value,
                passed=passed,
                details="pass" if passed else "normalized clause drift detected",
            )
        )

    baseline_links = {
        (link.from_clause_id, link.to_clause_id, link.link_type) for link in baseline_package.semantic_links
    }
    candidate_links = {
        (link.from_clause_id, link.to_clause_id, link.link_type)
        for link in candidate_package_metadata["semantic_links"]
    }
    passed_links = baseline_links == candidate_links
    cases.append(
        CrossVersionRegressionCase(
            case_id="LINK-SIGNATURE",
            clause_id="*",
            metric="semantic_link_signature",
            baseline_value=";".join(sorted(f"{a}->{b}:{c}" for a, b, c in baseline_links)),
            candidate_value=";".join(sorted(f"{a}->{b}:{c}" for a, b, c in candidate_links)),
            passed=passed_links,
            details="pass" if passed_links else "semantic link drift detected",
        )
    )

    return CrossVersionRegressionReport(
        baseline_package_id=baseline_package.package_id,
        candidate_package_id=str(candidate_package_metadata["package_id"]),
        generated_at_utc=generated_at_utc,
        drift_detected=any(not case.passed for case in cases),
        cases=cases,
    )


def generate_version_impact_report(
    *,
    baseline_package: StandardsPackage,
    candidate_package_metadata: dict[str, Any],
    project_clause_dependencies: list[ProjectClauseDependency],
    generated_at_utc: str,
) -> VersionImpactReport:
    """Generate impacted-project and selective re-verification scope for changed clauses."""
    baseline_signatures = {
        clause.clause_id: f"{clause.canonical_text}|{clause.canonical_equation}"
        for clause in baseline_package.normalized_clauses
    }
    candidate_signatures = {
        clause.clause_id: f"{clause.canonical_text}|{clause.canonical_equation}"
        for clause in candidate_package_metadata["normalized_clauses"]
    }
    all_clause_ids = sorted(set(baseline_signatures).union(candidate_signatures))
    changed_clause_ids = [
        clause_id
        for clause_id in all_clause_ids
        if baseline_signatures.get(clause_id) != candidate_signatures.get(clause_id)
    ]

    affected_projects: list[str] = []
    selective_reverification_scope: dict[str, list[str]] = {}
    changed_set = set(changed_clause_ids)
    for dependency in sorted(project_clause_dependencies, key=lambda item: item.project_id):
        impacted = sorted(changed_set.intersection(dependency.referenced_clause_ids))
        if impacted:
            affected_projects.append(dependency.project_id)
            selective_reverification_scope[dependency.project_id] = impacted

    return VersionImpactReport(
        baseline_package_id=baseline_package.package_id,
        candidate_package_id=str(candidate_package_metadata["package_id"]),
        generated_at_utc=generated_at_utc,
        changed_clause_ids=changed_clause_ids,
        affected_projects=affected_projects,
        selective_reverification_scope=selective_reverification_scope,
    )


def _parse_sources(source_documents: list[StandardSource]) -> list[ParsedClause]:
    pattern = re.compile(r"^(?P<clause>[A-Z]{2,4}-\d+[A-Z0-9\-]*)\s*:\s*(?P<body>.+)$")
    parsed: dict[str, ParsedClause] = {}

    for source in source_documents:
        for line_number, line in enumerate(source.content_text.splitlines(), start=1):
            normalized_line = " ".join(line.strip().split())
            if not normalized_line:
                continue
            if ":" not in normalized_line:
                raise ValueError(
                    "BL-005 parsing failed: malformed clause line "
                    f"in source {source.source_id} at line {line_number}."
                )
            match = pattern.match(normalized_line)
            if not match:
                raise ValueError(
                    "BL-005 parsing failed: malformed clause line "
                    f"in source {source.source_id} at line {line_number}."
                )

            clause_id = match.group("clause")
            if clause_id in parsed:
                raise ValueError(
                    "BL-005 parsing failed: duplicate clause_id "
                    f"{clause_id} encountered in source {source.source_id}."
                )
            body = match.group("body")
            equation = _extract_equation(body)
            cross_refs = sorted(set(re.findall(r"([A-Z]{2,4}-\d+[A-Z0-9\-]*)", body)))
            cross_refs = [ref for ref in cross_refs if ref != clause_id]
            parsed[clause_id] = ParsedClause(
                clause_id=clause_id,
                text=body,
                equation=equation,
                cross_references=cross_refs,
            )

    if not parsed:
        raise ValueError("BL-005 parsing failed: no clauses were extracted from source inputs.")

    return [parsed[key] for key in sorted(parsed)]


def _extract_equation(body: str) -> str | None:
    match = re.search(r"equation\s*=\s*([^;]+)", body, flags=re.IGNORECASE)
    if not match:
        return None
    return " ".join(match.group(1).strip().split())


def _normalize_clauses(parsed_clauses: list[ParsedClause]) -> list[NormalizedClause]:
    normalized: list[NormalizedClause] = []
    for clause in parsed_clauses:
        canonical_text = " ".join(clause.text.lower().split())
        canonical_equation = None
        canonical_variables: list[str] = []
        if clause.equation:
            canonical_equation = clause.equation.replace(" ", "")
            tokens = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", clause.equation))
            canonical_variables = sorted(token for token in tokens if len(token) <= 8)
        normalized.append(
            NormalizedClause(
                clause_id=clause.clause_id,
                canonical_text=canonical_text,
                canonical_equation=canonical_equation,
                canonical_variables=canonical_variables,
            )
        )
    return normalized


def _build_semantic_links(parsed_clauses: list[ParsedClause]) -> list[SemanticLink]:
    known = {clause.clause_id for clause in parsed_clauses}
    links: list[SemanticLink] = []
    for clause in parsed_clauses:
        for target in clause.cross_references:
            if target not in known:
                continue
            links.append(
                SemanticLink(
                    from_clause_id=clause.clause_id,
                    to_clause_id=target,
                    link_type="cross_reference",
                    reason="Cross-reference found in clause text.",
                )
            )

    links.sort(key=lambda link: (link.from_clause_id, link.to_clause_id, link.link_type))
    return links


def _validate_artifact_consistency(
    parsed_clauses: list[ParsedClause],
    normalized_clauses: list[NormalizedClause],
    semantic_links: list[SemanticLink],
) -> None:
    parsed_ids = {clause.clause_id for clause in parsed_clauses}
    normalized_ids = {clause.clause_id for clause in normalized_clauses}
    if parsed_ids != normalized_ids:
        raise ValueError("BL-005 validation failed: parsed/normalized clause IDs do not match.")

    for clause in parsed_clauses:
        if not clause.text.strip():
            raise ValueError(f"BL-005 validation failed: parsed clause {clause.clause_id} has empty text.")

    for link in semantic_links:
        if link.from_clause_id not in parsed_ids or link.to_clause_id not in parsed_ids:
            raise ValueError("BL-005 validation failed: semantic link references unknown clause IDs.")


def _run_regression_examples(
    *,
    regression_examples: list[RegressionExample],
    parsed_clauses: list[ParsedClause],
    semantic_links: list[SemanticLink],
) -> list[RegressionResult]:
    if not regression_examples:
        raise ValueError("BL-005 release gate failed: at least one regression example is required.")

    clause_ids = {clause.clause_id for clause in parsed_clauses}
    link_pairs = {(link.from_clause_id, link.to_clause_id) for link in semantic_links}
    results: list[RegressionResult] = []

    for example in regression_examples:
        if not example.example_id.strip():
            raise ValueError("BL-005 release gate failed: regression example_id must be non-empty.")

        missing_clauses = sorted(set(example.required_clause_ids) - clause_ids)
        missing_links = sorted(set(example.required_link_pairs) - link_pairs)
        passed = not missing_clauses and not missing_links

        details = "pass"
        if missing_clauses or missing_links:
            parts: list[str] = []
            if missing_clauses:
                parts.append(f"missing clauses={','.join(missing_clauses)}")
            if missing_links:
                pair_text = ",".join(f"{left}->{right}" for left, right in missing_links)
                parts.append(f"missing links={pair_text}")
            details = "; ".join(parts)

        results.append(RegressionResult(example_id=example.example_id, passed=passed, details=details))

    return sorted(results, key=lambda result: result.example_id)


def _build_source_fingerprints(source_documents: list[StandardSource]) -> list[dict[str, str]]:
    fingerprints: list[dict[str, str]] = []
    for source in sorted(source_documents, key=lambda source: source.source_id):
        checksum = hashlib.sha256(source.content_text.encode("utf-8")).hexdigest()
        fingerprints.append(
            {
                "source_id": source.source_id,
                "title": source.title,
                "publisher": source.publisher,
                "edition": source.edition,
                "revision": source.revision,
                "content_sha256": checksum,
            }
        )
    return fingerprints


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
