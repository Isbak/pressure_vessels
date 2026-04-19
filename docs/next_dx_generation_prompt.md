# Next DX Generation Prompt (Roadmap-Aligned)

DX-003 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-003 from docs/platform_roadmap.yaml.

Reference documents to use:
- docs/developer_experience_principles.md
- docs/runbooks/platform_runtime_stack_operations.md#deployment-readiness-checklist
- AGENT_GOVERNANCE.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is marked status: done.
3) DX-003 is the first item with status: todo.
4) DX-003 dependency is satisfied (depends_on: [DX-002]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-003+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-003 acceptance criteria:
- Fast local checks execute before commit.
- Hooks are documented and optionally installable.

DX-003 deliverables:
- pre-commit configuration
- Hook installation instructions

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-003 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-004 after DX-003 is done).
```

## Upcoming queue

After DX-003 is completed, the next queued item is DX-004 (depends on DX-001),
then DX-005 (depends on DX-004).
