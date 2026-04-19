"""Run end-to-end pressure vessel design and render a verification PDF.

This script wires the existing deterministic pipelines together:
  - BL-001 RequirementSet parsing
  - BL-002/BL-009 Design Basis + Applicability Matrix
  - BL-013 Material Basis resolution (via calculation pipeline)
  - BL-003 Calculation records + non-conformance list
  - BL-004 Compliance dossier
It then renders a human-readable verification PDF using reportlab.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pressure_vessels.calculation_pipeline import (  # noqa: E402
    CalculationRecordsArtifact,
    NonConformanceListArtifact,
    run_calculation_pipeline,
    write_calculation_artifacts,
)
from pressure_vessels.compliance_pipeline import (  # noqa: E402
    ComplianceDossierHuman,
    ComplianceDossierMachine,
    generate_compliance_dossier,
    write_compliance_artifacts,
)
from pressure_vessels.design_basis_pipeline import (  # noqa: E402
    ApplicabilityMatrix,
    DesignBasis,
    build_design_basis,
)
from pressure_vessels.geometry_module import GeometryInput  # noqa: E402
from pressure_vessels.requirements_pipeline import (  # noqa: E402
    RequirementSet,
    parse_prompt_to_requirement_set,
)

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


DEFAULT_PROMPT = (
    "Design a horizontal pressure vessel for propane storage, "
    "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
    "ASME Section VIII Div 1, corrosion allowance 3 mm."
)


@dataclass(frozen=True)
class DesignInputs:
    prompt: str
    geometry: GeometryInput


def build_default_design() -> DesignInputs:
    """Return a worked propane-storage design case with sensible geometry."""
    geometry = GeometryInput(
        schema_version="GeometryInput.v1",
        geometry_revision_id="REV-A",
        source_system="design_and_verify.py",
        source_model_sha256="0" * 64,
        shell_inside_diameter_m=2.0,
        shell_provided_thickness_m=0.035,
        head_inside_diameter_m=2.0,
        head_provided_thickness_m=0.030,
        nozzle_inside_diameter_m=0.35,
        nozzle_provided_thickness_m=0.012,
        external_pressure_pa=None,
    )
    return DesignInputs(prompt=DEFAULT_PROMPT, geometry=geometry)


def run_pipelines(
    design: DesignInputs,
    now_utc: datetime,
) -> tuple[
    RequirementSet,
    DesignBasis,
    ApplicabilityMatrix,
    CalculationRecordsArtifact,
    NonConformanceListArtifact,
    ComplianceDossierHuman,
    ComplianceDossierMachine,
]:
    requirement_set = parse_prompt_to_requirement_set(design.prompt, now_utc=now_utc)
    if requirement_set.downstream_blocked:
        missing = ", ".join(gap.field for gap in requirement_set.unresolved_gaps)
        raise SystemExit(f"Requirement parsing blocked; missing fields: {missing}")

    design_basis, applicability_matrix = build_design_basis(requirement_set, now_utc=now_utc)
    calc, non_conformance = run_calculation_pipeline(
        requirement_set=requirement_set,
        design_basis=design_basis,
        applicability_matrix=applicability_matrix,
        geometry_input=design.geometry,
        now_utc=now_utc,
    )
    human_dossier, machine_dossier = generate_compliance_dossier(
        requirement_set=requirement_set,
        design_basis=design_basis,
        applicability_matrix=applicability_matrix,
        calculation_records=calc,
        non_conformance_list=non_conformance,
        now_utc=now_utc,
    )
    return (
        requirement_set,
        design_basis,
        applicability_matrix,
        calc,
        non_conformance,
        human_dossier,
        machine_dossier,
    )


def _fmt_pa(value: float) -> str:
    return f"{value / 1e6:.3f} MPa"


def _fmt_mm(value_m: float) -> str:
    return f"{value_m * 1000:.2f} mm"


def _estimate_tan_tan_length_m(
    capacity_m3: float,
    shell_inside_diameter_m: float,
    head_inside_diameter_m: float,
) -> float:
    """Rough cylindrical-length estimate to help the reader size the drawing."""
    radius = shell_inside_diameter_m / 2.0
    head_volume_each = (math.pi / 6.0) * (head_inside_diameter_m ** 3) / 4.0
    cyl_volume = max(capacity_m3 - 2.0 * head_volume_each, 0.0)
    return cyl_volume / (math.pi * radius ** 2) if radius > 0 else 0.0


def render_verification_pdf(
    output_path: Path,
    *,
    requirement_set: RequirementSet,
    design_basis: DesignBasis,
    applicability_matrix: ApplicabilityMatrix,
    calc: CalculationRecordsArtifact,
    non_conformance: NonConformanceListArtifact,
    human_dossier: ComplianceDossierHuman,
    machine_dossier: ComplianceDossierMachine,
    geometry: GeometryInput,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Pressure Vessel Verification Report",
        author="pressure_vessels toolchain",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], spaceAfter=8, textColor=colors.HexColor("#1f2d3d")
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], spaceAfter=6, textColor=colors.HexColor("#1f2d3d")
    )
    body = ParagraphStyle("Body", parent=styles["BodyText"], spaceAfter=4, leading=13)
    mono = ParagraphStyle(
        "Mono", parent=styles["BodyText"], fontName="Courier", fontSize=8, leading=10, spaceAfter=3
    )

    elements = []

    elements.append(Paragraph("Pressure Vessel Verification Report", h1))
    elements.append(
        Paragraph(
            f"Generated (UTC): <b>{calc.generated_at_utc}</b> &nbsp;|&nbsp; "
            f"Standard: <b>{design_basis.primary_standard}</b> "
            f"({design_basis.primary_standard_version})",
            body,
        )
    )
    elements.append(Spacer(1, 6))

    reqs = requirement_set.requirements
    dp_pa = float(reqs["design_pressure"].value)
    dt_c = float(reqs["design_temperature"].value)
    cap_m3 = float(reqs["capacity"].value)
    ca_mm = float(reqs["corrosion_allowance"].value) if "corrosion_allowance" in reqs else None
    fluid = str(reqs["fluid"].value)

    estimated_len_m = _estimate_tan_tan_length_m(
        capacity_m3=cap_m3,
        shell_inside_diameter_m=geometry.shell_inside_diameter_m,
        head_inside_diameter_m=geometry.head_inside_diameter_m,
    )

    # Section 1: Design Prompt and Requirements
    elements.append(Paragraph("1. Design Prompt", h2))
    elements.append(Paragraph(f"<i>{requirement_set.input_prompt}</i>", body))

    elements.append(Paragraph("2. Normalized Requirements (BL-001)", h2))
    req_rows = [
        ["Field", "Value", "Unit", "Source text"],
        ["Fluid", fluid, "-", reqs["fluid"].source_text],
        ["Design pressure", f"{dp_pa:.0f}", "Pa", reqs["design_pressure"].source_text],
        ["Design temperature", f"{dt_c:.2f}", "C", reqs["design_temperature"].source_text],
        ["Capacity", f"{cap_m3:.3f}", "m3", reqs["capacity"].source_text],
        [
            "Corrosion allowance",
            f"{ca_mm:.2f}" if ca_mm is not None else "-",
            "mm",
            reqs["corrosion_allowance"].source_text if ca_mm is not None else "-",
        ],
        [
            "Code standard",
            str(reqs["code_standard"].value),
            "-",
            reqs["code_standard"].source_text,
        ],
    ]
    elements.append(_styled_table(req_rows, col_widths=[35 * mm, 45 * mm, 15 * mm, 75 * mm]))

    # Section 3: Design Basis
    elements.append(Paragraph("3. Design Basis (BL-002/BL-009)", h2))
    db_rows = [
        ["Primary standard", design_basis.primary_standard],
        ["Version", design_basis.primary_standard_version],
        ["Route ID", design_basis.selected_route_id],
        ["Signature", design_basis.deterministic_signature[:32] + "..."],
        ["Secondary standards", ", ".join(design_basis.secondary_standards) or "-"],
    ]
    elements.append(_kv_table(db_rows))
    if design_basis.assumptions:
        elements.append(Spacer(1, 3))
        elements.append(Paragraph("<b>Design Basis Assumptions</b>", body))
        for assumption in design_basis.assumptions:
            elements.append(Paragraph(f"&#8226; {assumption}", body))

    # Section 4: Material Basis + Geometry
    elements.append(Paragraph("4. Material and Geometry Basis", h2))
    mb = calc.material_basis
    mb_rows = [
        ["Material specification", str(mb["material_spec"])],
        ["Allowable stress (S)", _fmt_pa(float(mb["allowable_stress_pa"]))],
        ["Joint efficiency (E)", f"{float(mb['joint_efficiency']):.2f}"],
        [
            "Corrosion allowance",
            f"{float(mb['corrosion_allowance_m']) * 1000:.2f} mm "
            f"({mb['corrosion_allowance_policy']['policy_id']})",
        ],
        ["Standards package", str(mb["standards_package_ref"])],
    ]
    elements.append(_kv_table(mb_rows))
    elements.append(Spacer(1, 4))
    geo_rows = [
        ["Geometry revision", geometry.geometry_revision_id],
        ["Shell inside diameter", _fmt_mm(geometry.shell_inside_diameter_m)],
        ["Shell provided thickness", _fmt_mm(geometry.shell_provided_thickness_m)],
        ["Head inside diameter", _fmt_mm(geometry.head_inside_diameter_m)],
        ["Head provided thickness", _fmt_mm(geometry.head_provided_thickness_m)],
        ["Nozzle inside diameter", _fmt_mm(geometry.nozzle_inside_diameter_m)],
        ["Nozzle provided thickness", _fmt_mm(geometry.nozzle_provided_thickness_m)],
        ["Estimated T-T shell length (for capacity)", f"{estimated_len_m:.2f} m"],
    ]
    elements.append(_kv_table(geo_rows))

    # Section 5: Sizing & MAWP Checks
    elements.append(PageBreak())
    elements.append(Paragraph("5. ASME Division 1 Sizing & MAWP Checks (BL-003)", h2))
    check_rows = [[
        "Check ID",
        "Clause",
        "Component",
        "Required",
        "Provided",
        "Margin",
        "Utilization",
        "Status",
    ]]
    for record in calc.checks:
        if record.design_pressure_pa is not None and record.computed_mawp_pa is not None:
            required_str = _fmt_pa(record.design_pressure_pa)
            provided_str = _fmt_pa(record.computed_mawp_pa)
            margin_str = (
                _fmt_pa(record.pressure_margin_pa)
                if record.pressure_margin_pa is not None
                else "-"
            )
        else:
            required_str = _fmt_mm(record.required_thickness_m)
            provided_str = _fmt_mm(record.provided_thickness_m)
            margin_str = _fmt_mm(record.margin_m)
        status = "PASS" if record.pass_status else "FAIL"
        if record.pass_status and record.is_near_limit:
            status = "PASS*"
        check_rows.append(
            [
                record.check_id,
                record.clause_id,
                record.component,
                required_str,
                provided_str,
                margin_str,
                f"{record.utilization_ratio:.3f}",
                status,
            ]
        )
    elements.append(
        _styled_table(
            check_rows,
            col_widths=[
                38 * mm,
                18 * mm,
                18 * mm,
                25 * mm,
                25 * mm,
                22 * mm,
                22 * mm,
                15 * mm,
            ],
        )
    )
    elements.append(
        Paragraph(
            "PASS* indicates utilization at or above the near-limit threshold "
            f"({calc.checks[0].near_limit_threshold:.2f}); review before release.",
            body,
        )
    )

    # Section 6: Formulas and inputs per check
    elements.append(Paragraph("6. Formula Provenance per Check", h2))
    for record in calc.checks:
        elements.append(
            Paragraph(
                f"<b>{record.check_id}</b> &mdash; {record.formula}",
                body,
            )
        )
        inputs_str = ", ".join(
            f"{k}={v:.6g}" if isinstance(v, (int, float)) else f"{k}={v}"
            for k, v in sorted(record.inputs.items())
        )
        elements.append(Paragraph(inputs_str, mono))
        elements.append(
            Paragraph(
                f"canonical_sha256={record.reproducibility.canonical_payload_sha256}",
                mono,
            )
        )
        elements.append(Spacer(1, 2))

    # Section 7: Non-conformances
    elements.append(PageBreak())
    elements.append(Paragraph("7. Non-Conformances (BL-003)", h2))
    if not non_conformance.entries:
        elements.append(
            Paragraph(
                "No non-conformances detected. All sizing and MAWP checks satisfy their "
                "minimum requirements.",
                body,
            )
        )
    else:
        nc_rows = [["Check ID", "Clause", "Component", "Observed", "Required", "Severity"]]
        for entry in non_conformance.entries:
            nc_rows.append(
                [
                    entry.check_id,
                    entry.clause_id,
                    entry.component,
                    entry.observed,
                    entry.required,
                    entry.severity,
                ]
            )
        elements.append(_styled_table(nc_rows))

    # Section 8: Compliance matrix
    elements.append(Paragraph("8. Compliance Matrix (BL-004)", h2))
    matrix_rows = [["Clause", "Status", "Linked checks", "Justification"]]
    for row in machine_dossier.compliance_matrix:
        matrix_rows.append(
            [
                row.clause_id,
                row.status,
                ", ".join(row.check_ids) if row.check_ids else "-",
                row.justification,
            ]
        )
    elements.append(
        _styled_table(
            matrix_rows,
            col_widths=[22 * mm, 22 * mm, 50 * mm, 80 * mm],
        )
    )

    # Section 9: Reproducibility footer
    elements.append(Paragraph("9. Reproducibility & Audit Hashes", h2))
    hash_rows = [
        ["RequirementSet hash", requirement_set.deterministic_hash],
        ["Design basis signature", design_basis.deterministic_signature],
        ["Applicability matrix hash", applicability_matrix.deterministic_hash],
        ["Calculation records hash", calc.deterministic_hash],
        ["Non-conformance list hash", non_conformance.deterministic_hash],
        ["Compliance dossier (human)", human_dossier.deterministic_hash],
        ["Compliance dossier (machine)", machine_dossier.deterministic_hash],
    ]
    elements.append(_kv_table(hash_rows, mono_values=True))
    elements.append(Spacer(1, 6))
    elements.append(
        Paragraph(
            "<i>Advisory: outputs are generated by deterministic pipelines. "
            "Final responsibility for design compliance and certification remains "
            "with authorized professionals and governing bodies.</i>",
            body,
        )
    )

    doc.build(elements)


def _styled_table(rows, col_widths=None):
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2d3d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def _kv_table(rows, mono_values: bool = False):
    table = Table(rows, colWidths=[55 * mm, 120 * mm])
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f7")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if mono_values:
        style.append(("FONTNAME", (1, 0), (1, -1), "Courier"))
    table.setStyle(TableStyle(style))
    return table


def main() -> None:
    design = build_default_design()
    now_utc = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)

    (
        requirement_set,
        design_basis,
        applicability_matrix,
        calc,
        non_conformance,
        human_dossier,
        machine_dossier,
    ) = run_pipelines(design, now_utc)

    outdir = PROJECT_ROOT / "artifacts" / "design-runs" / "propane-18bar-30m3"
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / "RequirementSet.v1.json").write_text(
        json.dumps(requirement_set.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "DesignBasis.v1.json").write_text(
        json.dumps(design_basis.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "ApplicabilityMatrix.v1.json").write_text(
        json.dumps(applicability_matrix.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_calculation_artifacts(calc, non_conformance, outdir)
    write_compliance_artifacts(human_dossier, machine_dossier, outdir)

    pdf_path = outdir / "VerificationReport.pdf"
    render_verification_pdf(
        pdf_path,
        requirement_set=requirement_set,
        design_basis=design_basis,
        applicability_matrix=applicability_matrix,
        calc=calc,
        non_conformance=non_conformance,
        human_dossier=human_dossier,
        machine_dossier=machine_dossier,
        geometry=design.geometry,
    )

    overall = "PASS" if all(c.pass_status for c in calc.checks) else "FAIL"
    print(f"Overall verification: {overall}")
    print(f"Artifacts: {outdir}")
    print(f"PDF: {pdf_path}")


if __name__ == "__main__":
    main()
