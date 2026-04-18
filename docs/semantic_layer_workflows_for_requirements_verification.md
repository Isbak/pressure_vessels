# Semantic Layer for Requirements Verification Workflows

## 1) Purpose

This document defines a **semantic layer** that lets an agent-driven pressure vessel platform:

- translate user requirements into machine-verifiable constraints,
- execute standards-aware engineering workflows,
- trace each decision to governing clauses,
- and produce auditable evidence for certification.

It is intended to work alongside the architecture and ontology documents in this repository.

---

## 2) What the Semantic Layer Represents

The semantic layer is a normalized knowledge graph + rule model that maps:

1. **Requirement intent** (what the user/regulator wants),
2. **Standard obligations** (what code clauses require),
3. **Engineering models** (math/physics used for evaluation),
4. **Workflow states and decisions** (what was run, by whom, when),
5. **Evidence artifacts** (what proves compliance).

### 2.1 Canonical Semantic Objects

- **Requirement**: pressure, temperature, fluid, volume, corrosion allowance, design life, cyclic duty.
- **Design Basis**: selected jurisdiction, code, edition, assumptions, exclusion list.
- **ApplicableClause**: clause ID, conditions of applicability, required checks.
- **EngineeringModel**: formula set, validity domain, assumptions, variables, units.
- **VerificationTask**: deterministic check to run (input schema, output schema, pass/fail criteria).
- **DecisionRecord**: why a rule/model/task was selected.
- **EvidenceBundle**: calculation snapshot, report section, source clause, reviewer sign-off.

---

## 3) Workflow Set to Automate for Requirement Verification

The workflows below are the minimum automation backbone for certifiable outputs.

## Workflow A — Requirement Normalization and Gap Closure

**Goal:** convert free-form prompts/documents into a complete, structured requirement set.

**Inputs:** user prompt, P&ID tags (optional), client spec (optional), jurisdiction.

**Automated steps:**

1. Parse natural language into typed requirement candidates.
2. Resolve units and normalize to canonical units.
3. Detect missing mandatory fields (e.g., design pressure, temperature envelope, fluid hazard class).
4. Generate clarification questions and block downstream checks until resolved.
5. Assign requirement IDs and frozen revision hash.

**Outputs:** `RequirementSet.vX` + unresolved gap list.

---

## Workflow B — Governing Standard Selection and Applicability Mapping

**Goal:** determine which standards and sections apply for the exact equipment context.

**Inputs:** normalized requirements, jurisdiction, client constraints.

**Automated steps:**

1. Select primary governing code and edition.
2. Select secondary references (materials, welding, NDE, pressure testing, relief).
3. Evaluate applicability predicates per clause (service, category, geometry, limits).
4. Build an applicability matrix: `Clause -> Required/Not Required/Conditional`.
5. Record justification for any non-applicable clause.

**Outputs:** signed `DesignBasis` + `ApplicabilityMatrix`.

---

## Workflow C — Model Binding (Math/Physics/Empirical)

**Goal:** attach each required clause to an executable engineering model.

**Automated steps:**

1. For each required clause, select one approved `EngineeringModel` implementation.
2. Validate model domain (geometry/material/temp range) against current design.
3. Bind variable definitions and unit dimensions.
4. Register assumptions and conservative defaults.
5. Freeze model version references used for this design revision.

**Outputs:** `VerificationPlan` linking requirement IDs -> clause IDs -> model IDs.

---

## Workflow D — Deterministic Verification Execution

**Goal:** run clause-driven checks and generate reproducible pass/fail evidence.

**Automated steps:**

1. Execute thickness, MAWP, external pressure, reinforcement, and related checks.
2. Validate dimensional consistency and unit safety.
3. Compute margins and utilization ratios.
4. Flag failures, near-limits, and model domain violations.
5. Persist calculation input/output snapshots with reproducibility hashes.

**Outputs:** `CalculationRecords` + non-conformance list.

---

## Workflow E — Compliance Assembly and Audit Trace

**Goal:** package verifications into regulator/inspector-ready traceability.

**Automated steps:**

1. Build clause-by-clause compliance matrix.
2. Attach evidence links: requirement -> clause -> model -> result -> artifact.
3. Identify unresolved non-conformances and required dispositions.
4. Generate review checklist for human approvers.
5. Produce export package (human-readable + machine-readable).

**Outputs:** `ComplianceDossier` with complete trace graph.

---

## Workflow F — Change Impact and Re-Verification

**Goal:** ensure any requirement/code/model revision triggers correct re-check scope.

**Automated steps:**

1. Detect delta in requirements, code editions, material data, or model versions.
2. Propagate impact through dependency graph.
3. Compute minimal re-verification set.
4. Re-run affected tasks and compare against prior baseline.
5. Produce signed change impact report.

**Outputs:** `ImpactReport` + updated baseline status.

---

## 4) Standards Taxonomy the Semantic Layer Should Encode

The semantic layer should encode standards as typed obligations, not only text citations.

## 4.1 Primary Pressure Vessel Design Standards

- **ASME BPVC Section VIII Division 1**
  - Rule-based design-by-formula for many vessel configurations.
- **ASME BPVC Section VIII Division 2**
  - More rigorous design methods including design-by-analysis routes.
- **PED (Pressure Equipment Directive) context mapping**
  - Conformity assessment and essential safety requirements mapping.

## 4.2 Supporting Standards (Typical)

- Material specifications (e.g., ASME Section II references).
- Welding qualification and production welding references.
- NDE acceptance criteria references.
- Pressure testing and inspection requirements.
- Relief and overpressure protection references.

> Note: exact code editions and adopted references are project/jurisdiction-specific and must be captured explicitly in `DesignBasis`.

---

## 5) Math, Physics, and Other Model Families to Represent

Each `EngineeringModel` entry should be tagged with model family and validity envelope.

## 5.1 Core Mechanical Design Models

- **Thin/thick wall stress relations** (where code permits) for cylindrical/spherical shells.
- **Code formula models for required thickness** under internal pressure.
- **External pressure/buckling chart or equation-driven checks** as defined by governing rules.
- **Head-specific models** (ellipsoidal, hemispherical, torispherical geometries).
- **Nozzle opening reinforcement area replacement models**.
- **Flange/closure rating and gasket seating relationships** (where applicable by selected route).

## 5.2 Load and Strength Interaction Models

- Combined pressure + external loads (wind, seismic, nozzle loads) per selected acceptance route.
- Primary membrane/bending stress categorization when required by chosen standard path.
- Local discontinuity treatment via rule-based or analysis-based method.

## 5.3 Material and Temperature Models

- Allowable stress lookup models keyed by material, product form, and temperature.
- Temperature derating and low-temperature toughness eligibility checks.
- Corrosion allowance and minimum structural thickness logic.

## 5.4 Fatigue / Cyclic Service (When Applicable)

- Cycle counting category and screening thresholds.
- Fatigue curve-based usage factors for applicable standards/routes.
- Cumulative damage rules where explicitly required.

## 5.5 Safety/Relief Basis Models (Interface Layer)

- Overpressure scenario categorization and required relief philosophy mapping.
- Design pressure vs. set pressure consistency checks.
- Relief sizing model references (if included in project scope).

## 5.6 Numerical / High-Fidelity Models (Optional)

- FEA-based stress linearization workflows (for analysis routes).
- Buckling eigenvalue and nonlinear collapse workflows when required.
- CFD/thermal coupling only where performance requirements demand it.

---

## 6) Semantic Schema Additions (Recommended)

Add the following entities to the information model for better automation fidelity:

- `standard_package`
  - `package_id`, `code_name`, `edition`, `release_date`, `source_provenance`, `status`
- `applicability_rule`
  - `rule_id`, `clause_reference`, `predicate_expression`, `severity`, `rationale`
- `engineering_model`
  - `model_id`, `model_family`, `equation_set_ref`, `assumptions_json`, `validity_domain_json`, `unit_schema`
- `verification_task`
  - `task_id`, `requirement_id`, `clause_id`, `model_id`, `input_schema`, `acceptance_expression`
- `decision_record`
  - `decision_id`, `subject_type`, `subject_id`, `decision_text`, `approved_by`, `approved_at`

---

## 7) Automation Quality Gates

Every automated workflow execution should enforce:

1. **Unit-consistency gate**: no implicit unit conversions.
2. **Model-domain gate**: fail if inputs are outside validated envelope.
3. **Clause coverage gate**: fail if required clauses have no mapped task.
4. **Traceability gate**: fail if any pass/fail result lacks source clause + input snapshot.
5. **Determinism gate**: rerun with same inputs/version must match previous results.

---

## 8) Minimum Deliverables from the Semantic Layer

For each project revision, the platform should emit:

- A frozen `RequirementSet` and assumptions register.
- A signed `DesignBasis` with exact standards/editions.
- A `VerificationPlan` mapping requirements to executable checks.
- Reproducible `CalculationRecords` with pass/fail outcomes.
- Clause-by-clause `ComplianceMatrix` and evidence links.
- A `ChangeImpactReport` for every revision after baseline release.

This gives a complete digital thread from user intent to certifiable evidence.
