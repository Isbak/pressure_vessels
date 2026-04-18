# Audit Remediation Prompts — 2026-04-18

Each section below corresponds to a finding from `docs/full_repo_audit_2026-04-18.md`
(severity in parentheses). Prompts are self-contained: copy one into a fresh
Claude Code / Codex session and it should have enough context to execute.

Conventions for every prompt:

- Work on a new branch `claude/fix-<finding-id>` branched from `main`.
- Keep diffs minimal and scoped to the finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and `python scripts/check_ci_governance.py` before committing.
- Update `docs/development_backlog.yaml` only if the finding requires a backlog entry.
- Do not introduce new runtime dependencies without adding them to `pyproject.toml`.

---

## F1 — Reconcile backlog state with next-prompt pointer (Critical)

```text
You are fixing audit finding F1 in the `pressure_vessels` repo.

Problem:
`docs/next_code_generation_prompt.md:3` names BL-016 as the next item and claims
its dependencies (BL-004, BL-007, BL-012) are done. Inspection of
`docs/development_backlog.yaml` shows the status of BL-013, BL-014, BL-015 is
inconsistent with that narrative, so an agent reading the prompt could implement
out-of-order work.

Task:
1. Read `docs/development_backlog.yaml` end-to-end. For every item, verify:
   - `status` ∈ {todo, in_progress, done, blocked}
   - `depends_on` items exist and their status supports the claim
2. Produce a reconciliation table at `docs/roadmap_status_audit_2026-04-18.md`
   (append a new section, do not overwrite). Columns: id, title, current
   status, evidence (file/line or PR), corrected status, rationale.
3. Update `development_backlog.yaml` statuses to match reality. Do NOT invent
   completion — if evidence is missing, mark `todo` or `blocked` with a note.
4. Rewrite `docs/next_code_generation_prompt.md` to point at the first item
   whose dependencies are all genuinely `done`. Regenerate the dependency
   bullet list from the YAML (do not hand-edit the list).
5. Add a pytest in `tests/test_backlog_consistency.py` that parses the YAML
   and asserts every `todo`/`in_progress` item's `depends_on` are `done`.

Deliverable: one PR, no code changes outside the files listed above plus the
new test.
```

---

## F2 — Split tech stack into current vs. planned (Critical)

```text
You are fixing audit finding F2 in the `pressure_vessels` repo.

Problem:
`docs/tech-stack.md` declares an enterprise stack (Next.js, NestJS, Neo4j, vLLM,
Temporal, …) but `pyproject.toml:10` has `dependencies = []` and the repo
contains only Python modules. Readers assume components are deployed when they
are aspirational.

Task:
1. Restructure `docs/tech-stack.md` into two top-level sections:
   - `## Current` — only technologies actually imported/invoked in `src/`,
     `tests/`, `scripts/`, `.github/workflows/`. Cite each with a
     `file_path:line_number`.
   - `## Planned` — everything else, each item tagged with the backlog ID that
     introduces it (add a new backlog entry if none exists).
2. Add a one-line disclaimer at the top: "This document mixes deployed and
   planned capabilities; see section headers."
3. Add a CI check script `scripts/check_tech_stack.py` that parses the
   `## Current` section and fails if any listed dependency is absent from
   `pyproject.toml` or not imported anywhere under `src/`.
4. Wire the script into `.github/workflows/ci.yml` as a new job `tech-stack-check`.

Deliverable: updated doc, new script, new CI job, no changes to src/.
```

---

## F3 — Expand parametric tests for calculation_pipeline (High)

```text
You are fixing audit finding F3 in the `pressure_vessels` repo.

Problem:
`src/pressure_vessels/calculation_pipeline.py` (~47KB, 32 functions) is the
safety-critical ASME sizing core but `tests/test_calculation_pipeline.py` has
only a handful of explicit tests. No boundary/envelope coverage.

Task:
1. Read `_MODEL_VALIDITY_ENVELOPES` and every public function in
   `calculation_pipeline.py`. Enumerate input dimensions that have hard bounds
   (pressure, diameter, thickness, temperature, material allowable, etc.).
2. Add `tests/test_calculation_pipeline_envelopes.py` with pytest.parametrize
   suites covering, for each bounded input:
   - just-inside-bound values (must pass)
   - just-outside-bound values (must raise the documented exception)
   - zero and negative values where physically invalid
3. Add `tests/golden_examples/` containing at least three ASME Div. 1
   hand-calculation examples (cite source textbook/section in a `README.md`
   inside that directory) and a pytest that loads each example's JSON input
   and asserts the pipeline output matches reference values within the
   tolerance stated in the example.
4. Run coverage (`pytest --cov=pressure_vessels.calculation_pipeline`) and
   include the resulting percentage in the PR description. Target ≥ 90%.

Deliverable: new test files and golden fixtures only. Do not modify
`calculation_pipeline.py` except to fix defects the new tests surface; each
such fix gets its own commit with a message linking to the failing test.
```

---

## F4 — Vendor or remove root `markdownlint-cli2` (High)

```text
You are fixing audit finding F4 in the `pressure_vessels` repo.

Problem:
`./markdownlint-cli2` is committed at the repo root (0755, 5.6KB) and invoked
by `.github/workflows/ci.yml:25`. It shadows the npm package, is not in
`.gitignore`, and has no provenance metadata.

Preferred fix (A): install from npm.
1. Delete the root `markdownlint-cli2` file.
2. Add a `markdown-lint` job step in `.github/workflows/ci.yml` that runs
   `npx --yes markdownlint-cli2@<pinned-version> "**/*.md"`.
3. Record the pinned version in `.markdownlint-cli2.yaml` or a new
   `tools/versions.json`.

Alternative fix (B): formalize the vendored copy.
1. Move the file to `tools/markdownlint-cli2` and add `tools/VENDORED.md`
   recording origin URL, upstream version, SHA-256 of the file, and the
   rationale for vendoring.
2. Update `.github/workflows/ci.yml` to call `tools/markdownlint-cli2`.
3. Add a CI step that recomputes the SHA-256 and fails on mismatch.

Pick (A) unless offline CI is a hard requirement; in that case pick (B) and
state why in the PR description.

Deliverable: one PR implementing exactly one of the two options.
```

---

## F5 — Populate governance exceptions framework (High)

```text
You are fixing audit finding F5 in the `pressure_vessels` repo.

Problem:
`.github/governance/policy_exceptions.v1.json` is empty, but
`docs/governance/ci_governance_policy.v1.json` enforces six required gates
with no documented waiver path. `AGENT_GOVERNANCE.md` §6 mandates approvals
for exceptions.

Task:
1. Define the exception schema in
   `docs/governance/policy_exceptions_schema.v1.json` (JSON Schema). Required
   fields per entry: `id`, `gate`, `scope` (paths/globs), `justification`,
   `approver` (GitHub handle), `approved_at` (ISO-8601), `expires_at`,
   `linked_backlog_id`.
2. Replace the empty `.github/governance/policy_exceptions.v1.json` with a
   valid, empty-list document: `{"version":1,"exceptions":[]}`.
3. Update `scripts/check_ci_governance.py` to:
   - load the exceptions file,
   - validate it against the schema,
   - when a gate reports failure, allow the build if and only if a matching
     unexpired exception exists; log the exception ID and approver.
4. Document the request/approval workflow in `AGENT_GOVERNANCE.md` §11
   (rollout timeline) and cross-link from `docs/governance/README.md`
   (create if absent).
5. Add `tests/test_policy_exceptions.py` covering schema validation, expiry,
   scope matching, and the happy/failure paths in `check_ci_governance.py`.

Deliverable: schema, populated config, updated script, docs, tests.
```

---

## F6 — Expand agent playbooks (Medium)

```text
You are fixing audit finding F6 in the `pressure_vessels` repo.

Problem:
`.agents/codex/AGENTS.md` and `.agents/claude/CLAUDE.md` are ~5-line stubs.
`AGENT_GOVERNANCE.md:234–239` promises concrete detail there.

Task:
For each of the two files, produce sections:
1. Scope and out-of-scope tasks (explicit allowlist/denylist).
2. Canonical prompt templates for: backlog implementation, bug fix, doc
   update, audit, incident response. Each template must reference the
   relevant sections of `AGENT_GOVERNANCE.md`.
3. Escalation triggers (risk class, touched files, test failures) with the
   human reviewer role to page.
4. Rollback procedure: how to revert a merged agent change (git commands,
   approval chain, required notices).
5. Required artifacts per run (commit message format, PR template section,
   backlog updates).

Keep both files parallel in structure so diffs across agents are easy to
audit. No changes outside `.agents/`.
```

---

## F7 — Enforce artifact retention policy (Medium)

```text
You are fixing audit finding F7 in the `pressure_vessels` repo.

Problem:
`docs/governance/ci_governance_policy.v1.json` sets `artifact_retention_days`
but nothing enforces it; `.github/workflows/ci.yml:73` sets retention
independently.

Task:
1. In `.github/workflows/ci.yml`, read the retention value from the policy
   JSON at job start (use `jq`) and pass it to `actions/upload-artifact` via
   `retention-days: ${{ steps.policy.outputs.retention }}`.
2. Add a unit test `tests/test_ci_policy_wiring.py` that parses the workflow
   YAML and asserts the retention value is sourced from the policy file
   (string match on the expression).
3. Document in `docs/governance/README.md` that the policy file is the single
   source of truth for retention and that workflow changes must keep this
   linkage.

Deliverable: workflow update, test, docs update. No src/ changes.
```

---

## F8 — Remove silent MVP geometry fallback (Medium)

```text
You are fixing audit finding F8 in the `pressure_vessels` repo.

Problem:
`src/pressure_vessels/calculation_pipeline.py:21–31` applies `_MVP_DEFAULTS`
silently when `sizing_input` is missing, producing unrealistic designs without
user awareness.

Task:
1. Change the fallback path to raise a new
   `MissingGeometryInputError(ValueError)` declared in the same module, with
   a message naming the missing fields.
2. Keep `_MVP_DEFAULTS` available behind an explicit opt-in kwarg
   `use_mvp_defaults: bool = False`. When True, emit a `UserWarning` listing
   every defaulted field.
3. Update every caller in `src/` and `tests/` to pass real geometry inputs or
   opt in explicitly.
4. Add tests:
   - missing input without the flag raises `MissingGeometryInputError`,
   - with the flag, values match `_MVP_DEFAULTS` and a warning fires.
5. Note the behavior change in `docs/architecture.md` under a new
   "Breaking changes" subsection dated 2026-04-18.

Deliverable: code change, tests, docs note.
```

---

## F9 — Enforce PR checklist (Medium)

```text
You are fixing audit finding F9 in the `pressure_vessels` repo.

Problem:
`.github/pull_request_template.md:15–22` defines a checklist but nothing
blocks merge when items are unchecked.

Task:
1. Add a GitHub Actions workflow `.github/workflows/pr-checklist.yml` that
   runs on `pull_request` events (opened, edited, synchronize) and:
   - fetches the PR body,
   - asserts every line matching `^- \[x\]` for each required item defined
     in a new `.github/pr_required_checklist.yaml`,
   - fails with a clear message naming the missing items.
2. Create `.github/pr_required_checklist.yaml` listing the required items
   (risk class, agent author disclosure, approvals, tests run, docs
   updated).
3. Add a dry-run script `scripts/check_pr_checklist.py` so contributors can
   validate locally; include usage in `README.md` §Contributing.

Deliverable: workflow, config, script, README update.
```

---

## L-obs — Observations worth filing as backlog items (Low)

```text
You are filing low-severity audit observations as backlog items in the
`pressure_vessels` repo. Do not implement them now — only create tracking.

For each observation in `docs/full_repo_audit_2026-04-18.md` under
"Low / Observations":
1. Append a new entry to `docs/development_backlog.yaml` with:
   - `id`: next free BL-xxx
   - `title`: short imperative
   - `status`: todo
   - `depends_on`: []
   - `source`: "audit 2026-04-18, observation <n>"
2. Group related observations under a single item when the fix would be a
   single PR (e.g., `.gitignore` hardening).
3. Do not reorder existing entries.

Deliverable: YAML diff only, no code.
```

---

## Execution order

Recommended sequencing (parallelizable groups in brackets):

1. F1 (unblocks any future agent task)
2. [F4, F5, F9] — governance/CI hardening, independent
3. [F2, F6, F7] — documentation alignment, independent
4. F8 — behavior change, depends on F3 tests
5. F3 — test expansion, last so golden examples reflect F8's stricter API
6. L-obs — file whenever convenient

Every PR must reference this document: `Fixes F<n> per
docs/audit_remediation_prompts_2026-04-18.md`.
