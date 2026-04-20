from datetime import datetime, timezone
import json

import pytest

from pressure_vessels.standards_ingestion_pipeline import (
    RegressionExample,
    StandardSource,
    StandardsPackageCollisionError,
    run_standards_ingestion,
    write_standards_package,
)

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _sample_source() -> StandardSource:
    return StandardSource(
        source_id="ASME_BPVC_VIII_DIV1_2025_MAIN",
        title="ASME BPVC Section VIII Division 1 (sample)",
        publisher="ASME",
        edition="2025",
        revision="2025.2",
        content_text=(
            "UG-27: Cylindrical shell thickness for internal pressure; equation = "
            "t = (P*R)/(S*E-0.6*P); See UG-16.\n"
            "UG-16: Minimum thickness requirements for pressure parts.\n"
            "UG-32: Head thickness under internal pressure; equation = "
            "t = (0.885*P*D)/(2*S*E-0.2*P); See UG-27.\n"
        ),
    )


def _regression_examples() -> list[RegressionExample]:
    return [
        RegressionExample(
            example_id="REG-001",
            required_clause_ids=["UG-16", "UG-27", "UG-32"],
            required_link_pairs=[("UG-27", "UG-16"), ("UG-32", "UG-27")],
        )
    ]


def test_ingestion_pipeline_covers_parse_normalize_link_validate_and_release():
    package = run_standards_ingestion(
        source_documents=[_sample_source()],
        standard_key="ASME_VIII_1",
        standard_version="2025.2",
        release_label="r1",
        regression_examples=_regression_examples(),
        now_utc=FIXED_NOW,
    )

    assert package.schema_version == "StandardsPackage.v1"
    assert package.generated_at_utc == "2026-04-18T00:00:00+00:00"
    assert package.package_id == "ASME_VIII_1_2025.2_r1"
    assert package.immutable is True

    assert [clause.clause_id for clause in package.parsed_clauses] == ["UG-16", "UG-27", "UG-32"]
    assert [clause.clause_id for clause in package.normalized_clauses] == ["UG-16", "UG-27", "UG-32"]

    semantic_pairs = {(link.from_clause_id, link.to_clause_id) for link in package.semantic_links}
    assert semantic_pairs == {("UG-27", "UG-16"), ("UG-32", "UG-27")}

    assert package.regression_results
    assert all(result.passed for result in package.regression_results)


def test_ingestion_fails_closed_for_incomplete_source_metadata_and_content():
    incomplete_source = StandardSource(
        source_id="SOURCE-1",
        title="",
        publisher="ASME",
        edition="2025",
        revision="2025.2",
        content_text="",
    )

    with pytest.raises(ValueError, match="source intake failed"):
        run_standards_ingestion(
            source_documents=[incomplete_source],
            standard_key="ASME_VIII_1",
            standard_version="2025.2",
            release_label="r1",
            regression_examples=_regression_examples(),
            now_utc=FIXED_NOW,
        )


def test_ingestion_fails_closed_for_malformed_clause_line():
    malformed_source = StandardSource(
        source_id="SOURCE-1",
        title="Malformed sample",
        publisher="ASME",
        edition="2025",
        revision="2025.2",
        content_text=(
            "UG-16: Minimum thickness requirements for pressure parts.\n"
            "This line is not parseable as a clause.\n"
        ),
    )

    with pytest.raises(ValueError, match="parsing failed: malformed clause line"):
        run_standards_ingestion(
            source_documents=[malformed_source],
            standard_key="ASME_VIII_1",
            standard_version="2025.2",
            release_label="r1",
            regression_examples=_regression_examples(),
            now_utc=FIXED_NOW,
        )


def test_ingestion_fails_closed_for_duplicate_clause_ids():
    duplicate_clause_source = StandardSource(
        source_id="SOURCE-1",
        title="Duplicate clauses sample",
        publisher="ASME",
        edition="2025",
        revision="2025.2",
        content_text=(
            "UG-16: Minimum thickness requirements for pressure parts.\n"
            "UG-16: Duplicate row that should fail release.\n"
        ),
    )

    with pytest.raises(ValueError, match="parsing failed: duplicate clause_id UG-16"):
        run_standards_ingestion(
            source_documents=[duplicate_clause_source],
            standard_key="ASME_VIII_1",
            standard_version="2025.2",
            release_label="r1",
            regression_examples=_regression_examples(),
            now_utc=FIXED_NOW,
        )


def test_ingestion_release_gate_requires_regression_examples_to_pass():
    failing_regression = [
        RegressionExample(
            example_id="REG-FAIL",
            required_clause_ids=["UG-99"],
            required_link_pairs=[],
        )
    ]

    with pytest.raises(ValueError, match="release gate failed: regression examples failed"):
        run_standards_ingestion(
            source_documents=[_sample_source()],
            standard_key="ASME_VIII_1",
            standard_version="2025.2",
            release_label="r2",
            regression_examples=failing_regression,
            now_utc=FIXED_NOW,
        )


def test_write_standards_package_happy_path_is_byte_identical(tmp_path):
    package = run_standards_ingestion(
        source_documents=[_sample_source()],
        standard_key="ASME_VIII_1",
        standard_version="2025.2",
        release_label="r3",
        regression_examples=_regression_examples(),
        now_utc=FIXED_NOW,
    )

    first_path = write_standards_package(package, tmp_path)
    assert first_path.name == "ASME_VIII_1_2025.2_r3.json"
    expected_payload = package.to_json_dict()
    assert first_path.read_text(encoding="utf-8") == (json.dumps(expected_payload, indent=2, sort_keys=True) + "\n")


def test_write_standards_package_collision_raises_typed_error_and_preserves_artifact(tmp_path):
    package = run_standards_ingestion(
        source_documents=[_sample_source()],
        standard_key="ASME_VIII_1",
        standard_version="2025.2",
        release_label="r3",
        regression_examples=_regression_examples(),
        now_utc=FIXED_NOW,
    )

    first_path = write_standards_package(package, tmp_path)
    original_contents = first_path.read_text(encoding="utf-8")

    with pytest.raises(
        StandardsPackageCollisionError,
        match="Standards package collision for package_id=ASME_VIII_1_2025.2_r3",
    ):
        write_standards_package(package, tmp_path)

    assert first_path.read_text(encoding="utf-8") == original_contents


def test_write_standards_package_temp_file_removed_when_replace_fails(tmp_path, monkeypatch):
    package = run_standards_ingestion(
        source_documents=[_sample_source()],
        standard_key="ASME_VIII_1",
        standard_version="2025.2",
        release_label="r4",
        regression_examples=_regression_examples(),
        now_utc=FIXED_NOW,
    )
    artifact_path = tmp_path / f"{package.package_id}.json"

    def _boom(*_args, **_kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr("pressure_vessels.standards_ingestion_pipeline.os.replace", _boom)

    with pytest.raises(OSError, match="simulated replace failure"):
        write_standards_package(package, tmp_path)

    assert not artifact_path.exists()
    assert list(tmp_path.glob(f"{artifact_path.name}.tmp.*")) == []
