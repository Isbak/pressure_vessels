# BL-003 Golden Examples

These fixtures provide deterministic reference points for the ASME Section VIII Division 1
calculation pipeline implementation.

## Sources

1. **ASME Boiler & Pressure Vessel Code, Section VIII, Division 1 (2023)**:
   - UG-27(c)(1): Cylindrical shell under internal pressure.
   - UG-32: Formed heads under internal pressure.
   - UG-45: Nozzle neck minimum required thickness route.
   - UG-37: Reinforcement area adequacy check around openings.
2. **Dennis R. Moss, _Pressure Vessel Design Manual_, 4th Edition**:
   - Worked equation forms for Div. 1 pressure-thickness relationships and MAWP rearrangements.
3. **Eugene F. Megyesy, _Pressure Vessel Handbook_, 14th Edition**:
   - Independent handbook equation forms used to cross-check denominator/sign conventions at
     low-efficiency and high-corrosion edge conditions.

## Notes

- Example JSON files include SI input values and expected deterministic outputs from hand-set
  equation forms used in `calculation_pipeline.py`.
- Tolerances are case-specific and stored in each fixture under `tolerance`.
- `reject_envelope_cases.json` contains explicit invalid-domain/extrapolation vectors that must
  fail closed with model-domain gate errors.
- If any model-vs-reference delta exceeds tolerance, follow
  `docs/runbooks/validation_discrepancy_triage.md` before updating fixtures.
