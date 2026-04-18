# Independent Claude Review Guidance

Companion to [`AGENT_GOVERNANCE.md`](../../AGENT_GOVERNANCE.md) §4 (risk classification) and §10 (PR checklist). Defines the procedure for the independent Claude review required on medium/high-risk PRs.

## When required

Per the [risk matrix](../shared/risk-matrix.md):

- **Required**: medium and high risk PRs.
- **Optional**: low risk PRs (use only if the author requests adversarial feedback).

A Claude review is also required whenever a PR is reclassified upward during review.

## When not sufficient on its own

Independent Claude review **does not** substitute for any human approval defined in `AGENT_GOVERNANCE.md` §4. It is an additional gate, not a replacement.

## Trigger

Either:

1. PR author requests review by mentioning `@claude review` (or running the `/review` skill locally and pasting the output as a PR review).
2. Reviewer requests it on a PR that lacks one before approving.

The Claude review must be performed against the **current** head SHA. If new commits land after the review, request a delta review covering the new commits.

## Scope of the review

Cover, in this order:

1. **Correctness** — does the change do what the PR claims? Match the diff against the stated acceptance criteria / linked roadmap item (e.g. `BL-00x`).
2. **Compliance impact** — for calculation logic, confirm the formula, units, and rounding match the cited code section. Flag any deviation from ASME/PED references.
3. **Determinism & reproducibility** — for pipeline code, verify hashing, timestamp injection, and unit-normalization invariants are preserved.
4. **Security** — secrets, input validation at boundaries, dependency provenance, CI permission scope.
5. **Test coverage** — are the new behaviors covered? Are negative cases and edge cases (zero/negative inputs, unit conversions, missing fields) tested?
6. **Rollback** — is the change reversible by a single revert, or does it require data migration / artifact regeneration?

## Output format

Post the review as a single PR review (not loose comments) with this structure:

```text
Risk class (confirmed/disputed): <low|medium|high>
Head SHA reviewed: <sha>

Findings:
  [BLOCKER]  <file:line> — <issue> — <suggested fix>
  [MAJOR]    <file:line> — <issue> — <suggested fix>
  [MINOR]    <file:line> — <issue> — <suggested fix>
  [NIT]      <file:line> — <issue>

Recommendation: <go | no-go | go-with-conditions>
Conditions (if any): <bulleted>
```

Severity definitions:

- **BLOCKER** — must be fixed before merge (correctness, safety, security).
- **MAJOR** — should be fixed before merge; merge only with explicit human-reviewer override and rationale in the PR.
- **MINOR** — fix in this PR if cheap, otherwise file a follow-up.
- **NIT** — non-blocking style/clarity.

## Recording (audit)

The review itself is the audit record. Do not delete or rewrite a posted review; if the review needs correction, post a follow-up review that references the prior one. This satisfies `AGENT_GOVERNANCE.md` §8.

## Self-approval prohibition

Claude must not approve its own implementation PRs and must not mark a PR as mergeable. The recommendation field is advisory to the human approver.
