# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-037 — Add deterministic PDF generation and signature verification harness**.

```text
You are implementing backlog item **BL-037: Add deterministic PDF generation and signature verification harness** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-036` status is `done`.
- `BL-037` status is `todo`.
- `BL-037` dependencies are `BL-015`, and it is `done`.
- Therefore `BL-037` is the next eligible item.

Restate before coding:
- Item ID/title: BL-037 — Add deterministic PDF generation and signature verification harness
- depends_on: [BL-015]
- acceptance criteria:
  1) PDF outputs are byte-stable or normalized-hash stable for identical inputs.
  2) Signature validation checks pass for dossier and change-impact artifacts.
  3) CI fails on unsigned or tampered dossier payloads.
- deliverables:
  1) Deterministic PDF rendering verifier.
  2) Signature verification harness.
  3) CI gate for dossier signature integrity.

Repository constraints:
- Keep changes minimal and focused; implement BL-037 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `src/pressure_vessels/dossier_export_pipeline.py`
- `docs/interfaces/dossier_export_pipeline_contract.md`
- `docs/runbooks/dossier_export_pipeline_runbook.md`
- `artifacts/bl-007/CertificationDossierExportPackage.v1.sample.json`

Task:
1) Add deterministic PDF rendering verification for dossier exports.
2) Add signature verification checks for dossier and change-impact artifacts.
3) Add CI gate coverage for unsigned/tampered payload rejection.
4) Set `BL-037` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` to the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-037 is completed.

1. **BL-038** — Establish production security baseline for runtime interfaces (`todo`, deps: BL-022, BL-027)
2. **BL-039** — Define SLOs, telemetry, and incident response automation (`todo`, deps: BL-023, BL-026)
3. **BL-040** — Implement performance and scale benchmark suite (`todo`, deps: BL-017, BL-026)
4. **BL-041** — Expand engineering validation with independent references and edge envelopes (`todo`, deps: BL-003e, BL-017)
5. **BL-042** — Automate release pipeline and environment promotion gates (`blocked`, deps: BL-012, BL-026, BL-038)
