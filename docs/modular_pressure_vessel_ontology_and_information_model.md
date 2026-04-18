# Ontology and Information Model for a Modular Pressure Vessel

## 1) Purpose and Scope

This document defines:

- A **domain ontology** for modular pressure vessels (concepts, relationships, constraints).
- An **information model** (entities, attributes, identifiers, lifecycle state) that can be implemented in relational, document, or graph stores.

The model supports engineering design, fabrication, inspection, operations, and compliance traceability for vessels assembled from reusable modules.

---

## 2) Ontology (Conceptual Domain Model)

### 2.1 Core Classes

- **PressureVesselSystem**
  - A complete vessel assembly delivered for service.
- **VesselModule**
  - A replaceable or configurable module (e.g., shell course, head, nozzle cluster, support module).
- **PressureBoundaryComponent**
  - Any component that retains pressure (shell, head, nozzle neck, reinforcement pad, flange, blind).
- **NonPressureComponent**
  - Supports, skirts, lugs, platforms, insulation cladding, instrumentation brackets.
- **Joint**
  - A connection between components/modules (welded, bolted, flanged, threaded).
- **MaterialSpecification**
  - Material grade, product form, allowable stress source, heat treatment requirements.
- **DesignCondition**
  - Pressure, temperature, corrosion allowance, external loads, cyclic duty.
- **LoadCase**
  - Specific combinations of loads and boundary conditions.
- **CodeRule**
  - Clause from governing standards (e.g., ASME VIII Div 1/2, PED harmonized references).
- **Requirement**
  - Structured requirement statement with immutable ID, source, rationale, and revision.
- **DesignBasis**
  - Project-specific selection of code editions, jurisdiction, assumptions, and exclusions.
- **StandardPackage**
  - Versioned machine-readable package of clauses, variables, and applicability predicates.
- **ApplicabilityRule**
  - Executable predicate that decides whether a clause is required for a given context.
- **EngineeringModel**
  - Executable model implementing a standards obligation with assumptions and validity envelope.
- **VerificationTask**
  - Unit-safe deterministic check that binds requirement + clause + model + acceptance logic.
- **DecisionRecord**
  - Captured rationale/approval for applicability, assumptions, model selection, and disposition.
- **CalculationRecord**
  - Machine-readable calculation input/output and pass/fail disposition.
- **InspectionTestRecord**
  - NDE, hydrotest, pneumatic test, dimensional checks, hardness/PMI, etc.
- **ComplianceEvidence**
  - Trace links proving conformity: requirement -> rule -> calculation -> test -> signoff.
- **LifecycleEvent**
  - Fabrication, assembly, reconfiguration, repair, rerating, retirement.
- **DigitalArtifact**
  - Drawings, WPS/PQR, MTRs, certificates, reports, CAD, simulation files.

### 2.2 Class Hierarchy (Simplified)

- **Component**
  - PressureBoundaryComponent
    - ShellCourse
    - Head
    - Nozzle
    - Flange
    - ReinforcementPad
    - Closure
  - NonPressureComponent
    - Support
    - Platform
    - InsulationSystem
    - InstrumentBracket

- **Joint**
  - WeldedJoint
  - BoltedJoint
  - FlangedJoint
  - ThreadedJoint

- **InspectionTestRecord**
  - NDERecord
  - PressureTestRecord
  - DimensionalInspectionRecord
  - MaterialVerificationRecord

### 2.3 Key Relationships (Object Properties)

- `PressureVesselSystem definedBy Requirement`
- `Requirement constrainedBy DesignBasis`
- `DesignBasis adopts StandardPackage`
- `StandardPackage contains CodeRule`
- `CodeRule activatedBy ApplicabilityRule`
- `ApplicabilityRule instantiates VerificationTask`
- `VerificationTask executes EngineeringModel`
- `PressureVesselSystem hasModule VesselModule`
- `VesselModule hasComponent Component`
- `Component connectedBy Joint`
- `PressureBoundaryComponent madeOf MaterialSpecification`
- `PressureVesselSystem designedFor DesignCondition`
- `DesignCondition evaluatedBy LoadCase`
- `LoadCase checkedBy VerificationTask`
- `VerificationTask produces CalculationRecord`
- `CalculationRecord assesses CodeRule`
- `DecisionRecord governs (ApplicabilityRule | EngineeringModel | ComplianceEvidence)`
- `InspectionTestRecord verifies Component`
- `ComplianceEvidence references (CodeRule, CalculationRecord, InspectionTestRecord, DigitalArtifact)`
- `LifecycleEvent affects (PressureVesselSystem | VesselModule | Component)`
- `DigitalArtifact documents (Component | Joint | CalculationRecord | InspectionTestRecord)`

### 2.4 Data Properties (Selected)

- **Identifiers & versioning**
  - `globalId`, `moduleId`, `componentId`, `revision`, `configurationId`
- **Engineering values**
  - `designPressure`, `designTemperature`, `mawp`, `mdmt`, `corrosionAllowance`
  - `nominalThickness`, `requiredThickness`, `outerDiameter`, `length`, `volume`
- **Quality/compliance**
  - `acceptanceStatus`, `codeEdition`, `reviewer`, `approvalDate`
- **Lifecycle**
  - `effectiveFrom`, `effectiveTo`, `state` (Designed/Fabricated/Installed/InService/Retired)

### 2.5 Ontology Constraints (Examples)

- Every `PressureBoundaryComponent` **must** reference one `MaterialSpecification`.
- Every `PressureVesselSystem` **must** have at least one `DesignCondition`.
- Every active `LoadCase` **must** have at least one `CalculationRecord` with status.
- If a module is replaced (`LifecycleEvent = ModuleReplacement`), previous and new `configurationId` must be traceable.
- A `ComplianceEvidence` bundle is complete only if it includes at least one rule, one calculation, and one verification artifact.

---

## 3) Information Model (Logical Implementation)

Below is an implementation-friendly entity model.

## 3.1 Entities and Attributes

### `vessel_system`

- `vessel_id` (PK)
- `tag_number` (unique)
- `service_description`
- `jurisdiction`
- `governing_code`
- `code_edition`
- `design_pressure_value`, `design_pressure_unit`
- `design_temperature_value`, `design_temperature_unit`
- `mawp_value`, `mawp_unit`
- `status`
- `current_configuration_id`
- `created_at`, `updated_at`

### `requirement`

- `requirement_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `source_type` (prompt/spec/regulatory/assumption)
- `statement_text`
- `rationale`
- `priority` (mandatory/conditional/derived)
- `status` (draft/approved/superseded)
- `revision`
- `source_artifact_id` (FK -> digital_artifact, nullable)
- `created_at`, `updated_at`

### `design_basis`

- `design_basis_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `jurisdiction`
- `governing_code`
- `code_edition`
- `assumptions_json`
- `exclusions_json`
- `approved_by`
- `approved_at`
- `baseline_configuration_id` (FK -> configuration_baseline, nullable)

### `standard_package`

- `package_id` (PK)
- `code_name`
- `edition`
- `release_date`
- `source_provenance`
- `checksum`
- `status` (draft/released/deprecated)

### `applicability_rule`

- `applicability_rule_id` (PK)
- `package_id` (FK -> standard_package)
- `rule_id` (FK -> code_rule)
- `predicate_expression`
- `severity` (required/conditional/informative)
- `rationale`
- `version`
- `is_active` (bool)

### `engineering_model`

- `model_id` (PK)
- `model_name`
- `model_family` (formula/chart/analysis_lookup/fea)
- `equation_set_ref`
- `assumptions_json`
- `validity_domain_json`
- `unit_schema_json`
- `verification_status` (validated/provisional/deprecated)
- `version`

### `verification_task`

- `task_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `requirement_id` (FK -> requirement)
- `rule_id` (FK -> code_rule)
- `model_id` (FK -> engineering_model)
- `load_case_id` (FK -> load_case, nullable)
- `input_schema_json`
- `acceptance_expression`
- `task_status` (pending/passed/failed/blocked)
- `executed_at`

### `module`

- `module_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `module_type` (shell_course, head_set, nozzle_bank, support_set, internals_set)
- `module_name`
- `position_index`
- `interface_standard`
- `revision`
- `serial_number`
- `status`
- `effective_from`, `effective_to`

### `component`

- `component_id` (PK)
- `module_id` (FK -> module)
- `component_type`
- `description`
- `is_pressure_boundary` (bool)
- `material_spec_id` (FK -> material_specification, nullable for non-pressure parts)
- `nominal_thickness_value`, `nominal_thickness_unit`
- `required_thickness_value`, `required_thickness_unit`
- `diameter_value`, `diameter_unit`
- `length_value`, `length_unit`
- `corrosion_allowance_value`, `corrosion_allowance_unit`
- `revision`

### `joint`

- `joint_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `joint_type`
- `component_a_id` (FK -> component)
- `component_b_id` (FK -> component)
- `weld_procedure_id` (FK -> digital_artifact, nullable)
- `design_pressure_rating_value`, `design_pressure_rating_unit`
- `leak_tightness_class`

### `material_specification`

- `material_spec_id` (PK)
- `standard_name` (e.g., ASME SA-516)
- `grade`
- `product_form`
- `heat_treatment`
- `allowable_stress_basis`
- `temperature_limit_min`, `temperature_limit_max`
- `traceability_required` (bool)

### `design_condition`

- `design_condition_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `condition_name` (normal/upset/test/transport/seismic/fire)
- `internal_pressure_value`, `internal_pressure_unit`
- `external_pressure_value`, `external_pressure_unit`
- `design_temperature_value`, `design_temperature_unit`
- `cyclic_service_category`
- `fluid_group`
- `notes`

### `load_case`

- `load_case_id` (PK)
- `design_condition_id` (FK -> design_condition)
- `name`
- `description`
- `load_factors_json`
- `acceptance_criteria_json`

### `code_rule`

- `rule_id` (PK)
- `code_name`
- `edition`
- `clause_reference`
- `rule_type` (formula, limit, requirement, note)
- `machine_expression` (nullable)
- `applicability_json`

### `calculation_record`

- `calc_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `load_case_id` (FK -> load_case)
- `rule_id` (FK -> code_rule)
- `target_object_type` (vessel/module/component/joint)
- `target_object_id`
- `input_snapshot_json`
- `output_snapshot_json`
- `result_status` (pass/fail/needs_review)
- `performed_by` (agent/user/service)
- `performed_at`
- `reproducibility_hash`

### `inspection_test_record`

- `test_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `component_id` (FK -> component, nullable)
- `joint_id` (FK -> joint, nullable)
- `test_type`
- `procedure_ref`
- `acceptance_criteria_ref`
- `result`
- `performed_at`
- `inspector_id`
- `evidence_artifact_id` (FK -> digital_artifact)

### `compliance_evidence`

- `evidence_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `rule_id` (FK -> code_rule)
- `calc_id` (FK -> calculation_record, nullable)
- `test_id` (FK -> inspection_test_record, nullable)
- `artifact_id` (FK -> digital_artifact, nullable)
- `compliance_status`
- `reviewed_by`
- `reviewed_at`
- `comments`

### `decision_record`

- `decision_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `subject_type` (applicability/model/assumption/nonconformance)
- `subject_id`
- `decision_text`
- `decision_status` (accepted/rejected/needs_review)
- `approved_by`
- `approved_at`
- `artifact_id` (FK -> digital_artifact, nullable)

### `configuration_baseline`

- `configuration_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `name`
- `reason_for_change`
- `parent_configuration_id` (FK -> configuration_baseline, nullable)
- `released_by`
- `released_at`

### `lifecycle_event`

- `event_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `configuration_id` (FK -> configuration_baseline)
- `event_type` (fabricated/assembled/installed/inspected/reconfigured/repaired/rerated/retired)
- `event_timestamp`
- `actor`
- `summary`
- `artifact_id` (FK -> digital_artifact, nullable)

### `digital_artifact`

- `artifact_id` (PK)
- `vessel_id` (FK -> vessel_system)
- `artifact_type` (drawing/report/certificate/mtr/wps/pqr/cad/model/file)
- `title`
- `uri`
- `checksum`
- `version`
- `created_by`
- `created_at`

---

## 4) Cardinality Rules (Business Constraints)

- One `vessel_system` has **1..n** `module`.
- One `vessel_system` has **1..n** `requirement`.
- One `vessel_system` has exactly **1..n** approved `design_basis` revisions over lifecycle.
- One `module` has **1..n** `component`.
- One `component` can participate in **0..n** `joint`.
- One `design_condition` has **1..n** `load_case`.
- One `standard_package` has **1..n** `code_rule`.
- One `code_rule` has **0..n** `applicability_rule`.
- One `verification_task` maps to exactly **1** (`requirement`, `code_rule`, `engineering_model`) triplet.
- One `load_case` has **0..n** `verification_task` and **0..n** `calculation_record`.
- One `code_rule` can map to **0..n** `calculation_record` and **0..n** `compliance_evidence`.
- One `configuration_baseline` references a time-consistent set of modules/components.
- At least one `compliance_evidence` record is required per mandatory governing rule.

---

## 5) Reference JSON Payload (Example)

```json
{
  "vessel_id": "VSL-10045",
  "tag_number": "PV-201A",
  "governing_code": "ASME Section VIII Div 1",
  "code_edition": "2025",
  "requirements": [
    {
      "requirement_id": "REQ-SYS-001",
      "source_type": "prompt",
      "statement_text": "Maintain pressure boundary integrity for all approved load cases.",
      "priority": "mandatory",
      "revision": 1
    }
  ],
  "design_basis": {
    "design_basis_id": "DB-001",
    "jurisdiction": "US-TX",
    "governing_code": "ASME Section VIII Div 1",
    "code_edition": "2025",
    "assumptions": {"corrosion_allowance_mm": 3}
  },
  "design_conditions": [
    {
      "design_condition_id": "DC-NORMAL",
      "internal_pressure": {"value": 18, "unit": "bar"},
      "design_temperature": {"value": 65, "unit": "degC"}
    }
  ],
  "modules": [
    {
      "module_id": "MOD-SHELL-01",
      "module_type": "shell_course",
      "components": [
        {
          "component_id": "CMP-SHELL-01",
          "component_type": "ShellCourse",
          "is_pressure_boundary": true,
          "material": {"standard": "SA-516", "grade": "70"}
        }
      ]
    },
    {
      "module_id": "MOD-HEAD-FRONT",
      "module_type": "head_set"
    }
  ]
}
```

---

## 6) Recommended Storage Strategy

- **Graph layer** for ontology traversal and traceability (`rule -> calc -> test -> artifact`).
- **Relational core** for transactional integrity of engineering records.
- **Object store** for large artifacts (drawings, certificates, scans).
- **Immutable event log** for lifecycle and audit.

---

## 7) Minimum Viable Validation Rules

1. Unit consistency checks for every numeric engineering property.
2. Required fields by component type (e.g., shell requires diameter and thickness).
3. Mandatory material traceability for pressure-boundary parts.
4. No release of new configuration baseline without compliance evidence completeness check.
5. Any rerating event must trigger recalculation of all affected load cases.
6. Every mandatory `code_rule` in the selected `standard_package` must resolve to at least one `verification_task`.
7. Every `verification_task` must reference a validated `engineering_model` within model domain limits.
8. Any failed/blocked verification task must have a closed `decision_record` before baseline release.

---

## 8) Optional Extensions

- Reliability and risk ontology (failure modes, consequence class, RBI link).
- Manufacturing capability ontology (shop constraints, weld position limits).
- Cost model entities (material, labor, NDE, transport).
- Runtime telemetry integration (pressure/temperature historian for digital twin).
