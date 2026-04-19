# Next DX Generation Prompt (Roadmap-Aligned)

DX-007 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-007 from docs/platform_roadmap.yaml.

Reference documents to use:
- AGENT_GOVERNANCE.md#10-starter-governance-checklist
- docs/developer_experience_principles.md
- docs/developer_command_reference.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is marked status: done.
3) DX-003 is marked status: done.
4) DX-004 is marked status: done.
5) DX-005 is marked status: done.
6) DX-006 is marked status: done.
7) DX-007 is the first item with status: todo.
8) DX-007 dependencies are satisfied (depends_on: [DX-003, DX-006]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-008+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-007 acceptance criteria:
- CI emits machine-readable checklist/evidence outputs.
- PR templates can consume or link generated evidence.

DX-007 deliverables:
- Governance automation scripts
- Updated PR template guidance

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-007 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-008 after DX-007 is done).
```

## Upcoming queue

After DX-007 is completed, the next queued item is DX-008 (depends on DX-007),
then DX-009 (depends on DX-006).
