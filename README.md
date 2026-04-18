# Agent-Driven Pressure Vessel Design Tool

An end-to-end, agent-driven platform for pressure vessel engineering that transforms a natural-language design prompt into a traceable, certifiable engineering package.

This README describes a product blueprint for a modular toolchain that supports:

- Prompt-to-design automation

- Standards-aware calculations and checks

- Ingestion of new/updated design codes

- Design iteration and optimization

- Manufacturing package generation

- Certification-ready documentation and audit trails


Related repository docs:

- `docs/architecture.md`

- `docs/tech-stack.md`

- `docs/modular_pressure_vessel_ontology_and_information_model.md`

- `docs/semantic_layer_workflows_for_requirements_verification.md`

- `docs/decision-log/`

- `docs/interfaces/requirements_pipeline_contract.md`

- `docs/interfaces/design_basis_pipeline_contract.md`

- `docs/interfaces/calculation_pipeline_contract.md`

- `docs/interfaces/traceability_pipeline_contract.md`
- `docs/interfaces/change_impact_pipeline_contract.md`


---

## 1. Vision

Pressure vessel design is often split across spreadsheets, CAD files, code books, emails, and certification records. This tool unifies the workflow by using specialized software agents coordinated through a common orchestration layer.

**Goal:** Reduce cycle time from concept to certifiable design while increasing consistency, compliance, and traceability.

---

## 2. Scope: Prompt to Certification

### Input

A user supplies a prompt such as:

> "Design a horizontal pressure vessel for propane storage, 18 bar design pressure, 65°C design temperature, 30 m³ capacity, ASME Section VIII Div 1, corrosion allowance 3 mm, with full compliance report."

### Output

A complete package including:

- Requirement interpretation and assumptions

- Code-selected design basis

- Mechanical sizing calculations

- Material and thickness selection

- Nozzle/reinforcement checks

- Relief/safety basis summary

- Drawings and bill of materials hooks

- Compliance matrix against applicable code clauses

- Certification dossier with revision history


---

## 3. System Architecture (Modular)

The platform is split into independently deployable modules so teams can replace or upgrade components without rewriting the whole stack.

### Core Modules

1. **Prompt Intake & Requirement Parser**

   - Converts user prompt/documents into structured requirements.

   - Detects missing constraints and triggers clarification questions.

2. **Design Basis Engine**

   - Selects applicable standards, jurisdiction, design margins, load cases, and acceptance criteria.

   - Produces a formal Design Basis Memorandum (DBM).

3. **Standards Knowledge Layer**

   - Canonical model for standards clauses, equations, limits, and references.

   - Versioned and queryable by agents.

4. **Calculation Engine**

   - Runs shell/head/nozzle/thickness/MAWP checks.

   - Supports deterministic formulas, unit-safe computation, and reproducible outputs.

5. **Material & Corrosion Module**

   - Material compatibility, allowable stress lookup, corrosion allowance logic.

   - Optional integration with material databases.

6. **Geometry/CAD Interface**

   - Converts validated dimensions into parametric geometry.

   - Exports CAD-ready parameters and drawing metadata.

7. **Compliance & Traceability Engine**

   - Maps each result to code clauses.

   - Maintains evidence graph: requirement → calculation → output artifact.

8. **Optimization Agent (Optional)**

   - Multi-objective optimization (weight, cost, manufacturability).

   - Constrained by hard compliance rules.

9. **Certification Dossier Generator**

   - Produces report packs for Authorized Inspector / Notified Body review.

   - Includes signed assumptions, revision deltas, and checklist completion.

10. **Workflow Orchestrator**

    - Manages agent sequencing, retries, approvals, and human-in-the-loop gates.


---

## 4. Agent Roles

A practical decomposition of autonomous/semi-autonomous agents:

- **Requirements Agent** – Extracts and normalizes inputs.

- **Code Selection Agent** – Determines governing standards.

- **Mechanical Design Agent** – Performs sizing and stress-rule checks.

- **Materials Agent** – Selects compliant materials and checks limits.

- **Compliance Agent** – Generates clause-by-clause conformity matrix.

- **Documentation Agent** – Builds final report and certification package.

- **QA Agent** – Runs consistency checks across all outputs.


All agent actions should be logged with timestamps, model/version metadata, and source references.

---

## 5. Standards Ingestion (New Codes and Updates)

A dedicated ingestion pipeline keeps the system current as standards evolve.

### Ingestion Workflow

1. **Source Intake**

   - Accept standard documents (licensed PDFs, addenda, interpretations).

2. **Parsing & Structuring**

   - Extract clauses, equations, variable definitions, and applicability notes.

3. **Normalization**

   - Convert equations to machine-executable form with unit checks.

4. **Semantic Linking**

   - Link related clauses, exceptions, and cross-references.

5. **Validation**

   - Run regression test cases against benchmark examples.

6. **Versioning & Release**

   - Publish as immutable standards packages (e.g., `ASME_VIII_1_2025.2`).

7. **Impact Analysis**

   - Identify projects affected by standards updates and trigger re-checks.


### Governance Recommendations

- Require dual approval for standards package publication.

- Maintain provenance records for every parsed clause.

- Keep backward-compatible execution for legacy certified projects.


---

## 6. End-to-End Workflow

1. User submits design prompt and project constraints.

2. Requirements Agent creates structured spec and gap list.

3. Human confirms assumptions (if needed).

4. Design Basis Engine selects code/jurisdiction and load cases.

5. Mechanical + Materials agents generate candidate design.

6. Compliance Agent evaluates every required clause.

7. Optimization Agent refines within compliance envelope.

8. QA Agent runs consistency, units, and edge-case checks.

9. Documentation Agent generates certification dossier.

10. Final human sign-off and release.


---

## 7. Data Model (Suggested)

- **Project**: ID, client, jurisdiction, revision.

- **Requirements**: pressure, temperature, fluid, volume, corrosion allowance, duty.

- **Design Basis**: selected code, edition, assumptions, load combinations.

- **Calculations**: formula IDs, inputs, outputs, pass/fail.

- **Artifacts**: drawings, reports, BOM, inspection plans.

- **Compliance Records**: clause mapping, evidence links, reviewer sign-off.

- **Audit Log**: agent action history and approvals.


---

## 8. Certification Readiness Features

To support ASME/PED-style review workflows:

- Clause-level compliance matrix with evidence backlinks.

- Signed calculation snapshots (hash + timestamp).

- Material traceability references.

- Change impact report between revisions.

- Human approval checkpoints for critical decisions.

- Exportable package (PDF + machine-readable JSON).


---

## 9. Non-Functional Requirements

- **Determinism:** Same input/version produces same output.

- **Explainability:** Every result includes formula and clause provenance.

- **Security:** Role-based access and encrypted project artifacts.

- **Performance:** Fast iteration for conceptual design loops.

- **Extensibility:** Plugin interfaces for solvers, CAD, PLM, ERP.


---

## 10. Suggested Tech Stack (Example)

- **Orchestration:** Temporal / Dagster / custom workflow engine

- **Compute:** Python calculation services with unit libraries

- **Knowledge Store:** Graph + document store for standards clauses

- **API Layer:** REST/GraphQL for UI and integrations

- **UI:** Web dashboard for prompting, review, and sign-off

- **Reporting:** Template-driven PDF and JSON generation


---

## 11. Validation Strategy

- Golden test set from solved textbook and code examples.

- Cross-verification against legacy in-house calculations.

- Boundary testing for pressure/temperature/material extremes.

- Independent engineer review before production release.


---

## 12. Roadmap

### Phase 1: MVP

- Prompt parsing

- Core ASME Div 1 sizing checks

- Basic compliance report


### Phase 2: Production

- Standards ingestion pipeline

- Full traceability graph
- Change impact and selective re-verification with signed impact reports

- Certification dossier export


### Phase 3: Advanced

- Multi-standard support (ASME + PED + AD 2000, etc.)

- Cost/manufacturing optimization

- Enterprise integrations (PLM/ERP/QMS)


---

## 13. Agent Governance (Codex + Claude Code)

A governance starter policy is available at **`AGENT_GOVERNANCE.md`**. It defines:

- Risk-based merge gates

- Dual-agent workflow and separation of duties

- Required controls (branch protection, CI, secret scanning)

- Audit logging expectations and rollout plan


Adopt this as the baseline operating model for agent-assisted development in this project.

The recommended agentic repository layout is implemented under **`.agents/`**, **`.github/workflows/`**, and supporting docs in **`docs/`**.

Note: this repository currently implements a **starter baseline**; treat it as a foundation and evolve toward stricter policy-as-code and security assurance controls over time.

---

## 14. Disclaimer

This tool is intended to assist qualified engineers, not replace engineering judgment or statutory review. Final responsibility for design compliance and certification remains with authorized professionals and governing bodies.
