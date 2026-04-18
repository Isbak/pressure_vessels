# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-019**.

```text
You are implementing backlog item **BL-019: Automate governance and CI control drift review** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved from YAML on 2026-04-18):
- `BL-019` status is `todo`.
- `BL-019` dependencies: none.
- This makes `BL-019` the first `todo`/`in_progress` item whose `depends_on` set is fully `done`.

Restate before coding:
- Item ID/title: BL-019 — Automate governance and CI control drift review
- depends_on: []
- source: audit 2026-04-18, observation 1 and 3

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `docs/governance/ci_governance_policy.v1.json`
- `scripts/check_ci_governance.py`
- `.github/workflows/ci.yml`
- `tests/test_ci_policy_wiring.py`

Task:
1) Implement BL-019 behavior using existing repository patterns.
2) Add or strengthen automated checks for governance/CI control drift.
3) Add/extend tests under `tests/` for new behavior.
4) Update related docs under `docs/` if contracts change.
5) Update `docs/development_backlog.yaml` status for BL-019 when complete.
6) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
