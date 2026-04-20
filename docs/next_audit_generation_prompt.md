# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-001** from
`docs/audit_findings_2026-04-20.yaml` (severity: critical, status: todo,
no open dependencies).

```text
Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-20.yaml with
   status: todo.
2) Verify every depends_on entry has status: done.
3) Implement only that finding with minimal, focused changes.
4) Update the finding's status to done in the YAML when the PR merges.
```

## Prompt — AF-001 Harden concurrent standards-package writes (Critical)

```text
You are fixing audit finding AF-001 in the `pressure_vessels` repo.

Problem:
`src/pressure_vessels/standards_ingestion_pipeline.py:180` creates immutable
package artifacts with `open(path, "x")`. Two concurrent ingestion runs for
the same `package_id` race: the second raises a bare `FileExistsError`
mid-write without cleanup or locking, leaving the artifact store in an
ambiguous state. This undermines the immutability guarantee that the
calculation and compliance pipelines rely on (BL-005).

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-001` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-001 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Read the current write path in
   `src/pressure_vessels/standards_ingestion_pipeline.py` end-to-end.
   Identify every call site that materializes a package artifact on disk.
2. Introduce a private helper (e.g., `_atomic_write_json`) that:
   - writes to a sibling temp file in the same directory
     (`<target>.tmp.<uuid>`),
   - `os.fsync`s the file handle before close,
   - uses `os.replace` to publish atomically,
   - removes the temp file on any failure (try/finally),
   - refuses to overwrite an existing target and raises a new typed
     exception `StandardsPackageCollisionError(FileExistsError)` declared in
     the same module, with a message naming the colliding `package_id` and
     path.
3. Replace the `open(path, "x")` call at the current line 180 (and any
   sibling writes) with the helper. No behavior change for the happy path;
   collisions now raise the typed exception.
4. Update the runbook at
   `docs/runbooks/standards_ingestion_pipeline_runbook.md` to document the
   collision exception and the atomic publish guarantee.
5. Update `docs/audit_findings_2026-04-20.yaml`:
   - set AF-001 `status: done`,
   - leave AF-009 `status: todo` (its stress test belongs in a separate PR).
6. Tests — add to `tests/test_standards_ingestion_pipeline.py` (or a sibling
   file) covering:
   - happy path writes succeed and produce a byte-identical artifact,
   - a second write to the same `package_id` raises
     `StandardsPackageCollisionError` and leaves the original artifact
     untouched,
   - a simulated failure between temp-write and `os.replace` (use
     monkeypatch on `os.replace`) leaves no `.tmp.*` files behind and no
     published artifact.

Out of scope (tracked separately):
- The concurrency stress test itself — that is AF-009.
- Versioning of material allowables — that is AF-005.

Deliverable: one PR touching
`src/pressure_vessels/standards_ingestion_pipeline.py`,
`docs/runbooks/standards_ingestion_pipeline_runbook.md`,
`docs/audit_findings_2026-04-20.yaml`, and the new/updated tests. No other
files.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` `execution_order`:

1. **AF-001** — Harden concurrent standards-package writes *(this prompt)*
2. **AF-009** — Add concurrent-write stress test (depends on AF-001)
3. **AF-002** — Validate geometry adapter inputs with typed errors
4. **AF-004** — Fail closed on MVP geometry defaults in production mode
5. **AF-003** — Document and justify safety-critical rounding precision
6. **AF-008** — Replace inf utilization sentinel (depends on AF-003)

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
