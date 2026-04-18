# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e, BL-004, BL-005, BL-006, BL-007, BL-008, BL-009, BL-010, BL-011
- Next item to implement: BL-012
- BL-012 title: Enforce governance gates in CI
- BL-012 depends_on: none
- BL-012 acceptance criteria:

  1) CI enforces test/lint/security/reporting requirements from governance policy.
  2) Build/test artifacts are retained for auditability.
  3) Policy exceptions require explicit approval record.

- BL-012 deliverables:

  - CI policy checks
  - Artifact retention configuration

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

1) Implement BL-012 CI governance gating behavior using existing repository patterns.
2) Add policy enforcement checks for test/lint/security/reporting requirements.
3) Add artifact retention configuration and explicit policy exception approval recording.
4) Add/extend tests under `tests/` for CI gate evaluation and policy exception handling logic.
5) Update related architecture/interface docs under `docs/` to describe BL-012 governance schemas and CI operational expectations.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
