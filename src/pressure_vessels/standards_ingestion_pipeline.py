"""Deterministic standards ingestion pipeline for BL-005."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

STANDARDS_PACKAGE_VERSION = "StandardsPackage.v1"


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
            "deterministic_hash": self.deterministic_hash,
        }


def run_standards_ingestion(
    *,
    source_documents: list[StandardSource],
    standard_key: str,
    standard_version: str,
    release_label: str,
    regression_examples: list[RegressionExample],
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
        deterministic_hash=deterministic_hash,
    )


def write_standards_package(package: StandardsPackage, directory: str | Path) -> Path:
    """Persist an immutable standards package; fail if package ID already exists."""
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{package.package_id}.json"
    payload = json.dumps(package.to_json_dict(), indent=2, sort_keys=True)
    with output_path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.write("\n")
    return output_path


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


def _parse_sources(source_documents: list[StandardSource]) -> list[ParsedClause]:
    pattern = re.compile(r"^(?P<clause>[A-Z]{2,4}-\d+[A-Z0-9\-]*)\s*:\s*(?P<body>.+)$")
    parsed: dict[str, ParsedClause] = {}

    for source in source_documents:
        for line in source.content_text.splitlines():
            normalized_line = " ".join(line.strip().split())
            if not normalized_line:
                continue
            match = pattern.match(normalized_line)
            if not match:
                continue

            clause_id = match.group("clause")
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
