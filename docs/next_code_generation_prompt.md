# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e, BL-004, BL-005, BL-006, BL-007
- Next item to implement: BL-008
- BL-008 title: Add change impact and selective re-verification
- BL-008 depends_on: BL-003, BL-006 (already done)
- BL-008 acceptance criteria:

  1) Requirement/code/model deltas are detected automatically.
  2) Minimal re-verification set is computed and executed.
  3) Signed change impact report is generated for each revision delta.

- BL-008 deliverables:

  - ImpactReport artifact
  - Updated baseline status

Repository constraints:

- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Existing relevant files:

- `scripts/`
- `docs/`
- `src/pressure_vessels/`
- `tests/`
- `README.md`

Task:

1) Implement BL-008 change-impact and selective re-verification behavior using existing repository patterns.
2) Add deterministic delta detection for requirement/code/model changes tied to revisioned traceability artifacts.
3) Compute and execute a minimal re-verification set and persist an explicit baseline update decision.
4) Generate a signed change impact report artifact per revision delta.
5) Add/extend tests under `tests/` for deterministic delta detection, selective re-verification scope, and signed impact report evidence links.
6) Update related architecture/interface docs under `docs/` to describe BL-008 schema and usage, and persist sample artifacts under `artifacts/` if introduced.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
