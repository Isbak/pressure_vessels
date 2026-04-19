# Next DX Generation Prompt (Roadmap-Aligned)

DX-002 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-002 from docs/platform_roadmap.yaml.

Reference documents to use:
- docs/developer_experience_principles.md
- docs/runbooks/platform_runtime_stack_operations.md#deployment-readiness-checklist
- AGENT_GOVERNANCE.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is the first item with status: todo.
3) DX-002 dependency is satisfied (depends_on: [DX-001]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-003+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-002 acceptance criteria:
- Common workflows (test, governance checks, stack checks) use short aliases.
- CI command parity documented for local runs.

DX-002 deliverables:
- Task runner config
- Developer command reference

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-002 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-003 after DX-002 is done).
```

## Upcoming queue

After DX-002 is completed, the next queued item is DX-003 (depends on DX-002),
then DX-004 (depends on DX-001 and is already dependency-eligible).
