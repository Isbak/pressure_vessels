# Validation Discrepancy Triage Runbook (BL-041)

Use this runbook when any golden/reference case in `tests/golden_examples/` exceeds its fixture tolerance.

## Trigger

Start triage when a validation test fails with an absolute delta greater than the fixture's `tolerance` field.

## Inputs Required

- Failing test output (`pytest -k golden_examples -vv`).
- The specific fixture JSON from `tests/golden_examples/`.
- Current `src/pressure_vessels/calculation_pipeline.py` revision.
- Clause references declared in the fixture `source` field.

## Triage Workflow

1. **Reproduce deterministically**
   - Re-run only the failing case with fixed timestamp inputs.
   - Confirm failure is repeatable across at least two runs.
2. **Localize the first divergent check**
   - Compare actual vs expected by `check_id`.
   - Capture the earliest route where delta exceeds tolerance (UG-27/UG-32/UG-45/UG-37/MAWP).
3. **Classify discrepancy type**
   - **Model regression**: formula/rounding/ordering logic changed in code.
   - **Reference defect**: fixture typo or stale expected value.
   - **Domain misuse**: case should be reject-domain but was modeled as in-envelope.
4. **Apply disposition rule**
   - If model regression is unintended: fix code and keep existing fixture.
   - If model regression is intentional and approved: update fixture expected outputs and record rationale in commit message.
   - If reference defect: correct fixture metadata/value and add a focused test assertion preventing recurrence.
   - If domain misuse: move/duplicate case into reject suite (`reject_envelope_cases.json`) and enforce fail-closed behavior.
5. **Evidence and closure**
   - Include before/after delta values in PR summary.
   - Ensure `tests/test_calculation_pipeline_golden_examples.py` passes.
   - Update `tests/golden_examples/README.md` if source attribution or tolerance policy changed.

## Escalation Criteria

Escalate to engineering review if any apply:

- Absolute delta exceeds `10 x tolerance`.
- More than one clause route diverges in the same fixture.
- Divergence alters pass/fail status of any compliance-critical check.

## Required Artifacts in PR

- Link to failing and passing test command output.
- Fixture diff (if changed) with deterministic rationale.
- Contract/doc update when discrepancy implies interface or envelope interpretation change.
