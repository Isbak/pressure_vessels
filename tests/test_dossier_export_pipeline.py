import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from pressure_vessels.calculation_pipeline import run_calculation_pipeline
from pressure_vessels.change_impact_pipeline import (
    build_revision_trace_snapshot,
    generate_change_impact_report,
)
from pressure_vessels.compliance_pipeline import generate_compliance_dossier
from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.dossier_export_pipeline import (
    CANONICAL_DOSSIER_PDF_RENDER_VERSION,
    CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION,
    CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION,
    generate_certification_dossier_export,
    write_certification_dossier_export,
)
from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set
from pressure_vessels.traceability_pipeline import build_traceability_graph_revision

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _default_prompt() -> str:
    return (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )


def _build_export_inputs(prompt: str):
    requirement_set = parse_prompt_to_requirement_set(prompt, now_utc=FIXED_NOW)
    design_basis, matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)
    calculation_records, non_conformance = run_calculation_pipeline(
        requirement_set,
        design_basis,
        matrix,
        now_utc=FIXED_NOW,
        use_mvp_defaults=True,
    )
    compliance_human, compliance_machine = generate_compliance_dossier(
        requirement_set,
        design_basis,
        matrix,
        calculation_records,
        non_conformance,
        now_utc=FIXED_NOW,
    )
    graph = build_traceability_graph_revision(
        requirement_set,
        design_basis,
        matrix,
        compliance_machine,
        revision_id="REV-0007",
        now_utc=FIXED_NOW,
    )
    previous_graph = build_traceability_graph_revision(
        requirement_set,
        design_basis,
        matrix,
        compliance_machine,
        revision_id="REV-0006",
        now_utc=FIXED_NOW,
    )
    previous_snapshot = build_revision_trace_snapshot(
        revision_id="REV-0006",
        previous_revision_id=None,
        requirement_set_hash=requirement_set.deterministic_hash,
        calculation_records_hash=calculation_records.deterministic_hash,
        traceability_graph_hash=previous_graph.deterministic_hash,
        code_fingerprint="git:bl015",
        model_fingerprint="models:v1",
    )
    current_snapshot = build_revision_trace_snapshot(
        revision_id="REV-0007",
        previous_revision_id="REV-0006",
        requirement_set_hash=requirement_set.deterministic_hash,
        calculation_records_hash=calculation_records.deterministic_hash,
        traceability_graph_hash=graph.deterministic_hash,
        code_fingerprint="git:bl015",
        model_fingerprint="models:v1",
    )
    impact_report = generate_change_impact_report(
        previous_snapshot,
        current_snapshot,
        previous_graph,
        graph,
        calculation_records,
        signing_key_ref="kms://pressure-vessels/bl-008",
        now_utc=FIXED_NOW,
    )

    return (
        requirement_set,
        design_basis,
        matrix,
        calculation_records,
        non_conformance,
        compliance_human,
        compliance_machine,
        graph,
        impact_report,
    )


def test_export_package_includes_machine_json_pdf_payload_and_required_evidence_links():
    inputs = _build_export_inputs(_default_prompt())

    export_package = generate_certification_dossier_export(
        *inputs,
        revision_id="REV-0007",
        previous_revision_id="REV-0006",
        now_utc=FIXED_NOW,
    )

    payload = export_package.to_json_dict()

    assert payload["schema_version"] == CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION
    assert payload["pdf_payload"]["schema_version"] == CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION
    assert payload["change_impact_report"]["schema_version"] == "ImpactReport.v1"
    assert payload["inspector_regulator_workflow"]
    assert payload["workflow_signoff_transitions"]
    assert payload["canonical_pdf_render"]["schema_version"] == CANONICAL_DOSSIER_PDF_RENDER_VERSION
    assert payload["canonical_pdf_render"]["content"].startswith("%PDF-1.4")
    assert all(step["role"] in {"design_authority", "authorized_inspector", "regulator"} for step in payload["inspector_regulator_workflow"])
    assert all(transition["required_evidence_refs"] for transition in payload["workflow_signoff_transitions"])

    assert payload["signed_calculation_snapshots"]
    for snapshot in payload["signed_calculation_snapshots"]:
        assert snapshot["artifact_ref"].startswith("CalculationRecords.v1#")
        assert snapshot["signature_ref"].startswith("sha256:")

    refs = set(payload["package_artifact_refs"])
    assert any(ref.startswith("CertificationDossierExportPackage.v1#") for ref in refs)
    assert any(ref.startswith("CertificationDossierPDFPayload.v1#") for ref in refs)
    assert any(ref.startswith("CanonicalDossierPDF.v1#") for ref in refs)
    assert any(ref.startswith("ImpactReport.v1#") for ref in refs)


def test_export_package_is_deterministic_with_fixed_timestamp():
    inputs = _build_export_inputs(_default_prompt())

    package_a = generate_certification_dossier_export(
        *inputs,
        revision_id="REV-0007",
        now_utc=FIXED_NOW,
    )
    package_b = generate_certification_dossier_export(
        *inputs,
        revision_id="REV-0007",
        now_utc=FIXED_NOW,
    )

    assert package_a.to_json_dict() == package_b.to_json_dict()
    assert package_a.deterministic_hash == package_b.deterministic_hash
    assert package_a.reproducibility == {
        "canonicalization": "json.sort_keys+compact",
        "hash_algorithm": "sha256",
    }


def test_export_gate_rejects_traceability_compliance_hash_mismatch():
    inputs = _build_export_inputs(_default_prompt())
    (
        requirement_set,
        design_basis,
        matrix,
        calculation_records,
        non_conformance,
        compliance_human,
        compliance_machine,
        graph,
        impact_report,
    ) = inputs
    corrupted_graph = replace(graph, source_compliance_dossier_hash="bad-hash")

    with pytest.raises(ValueError, match="traceability graph compliance hash mismatch"):
        generate_certification_dossier_export(
            requirement_set,
            design_basis,
            matrix,
            calculation_records,
            non_conformance,
            compliance_human,
            compliance_machine,
            corrupted_graph,
            impact_report,
            revision_id="REV-0007",
            now_utc=FIXED_NOW,
        )


def test_export_gate_rejects_impact_report_revision_mismatch():
    inputs = _build_export_inputs(_default_prompt())

    with pytest.raises(ValueError, match="impact report revision mismatch"):
        generate_certification_dossier_export(
            *inputs,
            revision_id="REV-0999",
            now_utc=FIXED_NOW,
        )


def test_write_export_package_persists_canonical_json(tmp_path):
    inputs = _build_export_inputs(_default_prompt())
    export_package = generate_certification_dossier_export(
        *inputs,
        revision_id="REV-0007",
        now_utc=FIXED_NOW,
    )

    package_path, pdf_payload_path, canonical_pdf_path = write_certification_dossier_export(export_package, tmp_path)

    assert package_path.name == "CertificationDossierExportPackage.v1.json"
    assert pdf_payload_path.name == "CertificationDossierPDFPayload.v1.json"
    assert canonical_pdf_path.name == "CanonicalDossierPDF.v1.pdf"

    with package_path.open() as package_file:
        package_on_disk = json.load(package_file)
    with pdf_payload_path.open() as pdf_file:
        pdf_payload_on_disk = json.load(pdf_file)
    canonical_pdf_on_disk = canonical_pdf_path.read_text(encoding="utf-8")

    assert package_on_disk == export_package.to_json_dict()
    assert pdf_payload_on_disk == export_package.pdf_payload
    assert canonical_pdf_on_disk == export_package.canonical_pdf_render["content"]
