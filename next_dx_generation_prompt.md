# Next DX Generation Prompt (Roadmap-Aligned)

DX-001 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-001 from docs/platform_roadmap.yaml.

Reference documents to use:
- docs/developer_experience_principles.md
- AGENT_GOVERNANCE.md
- README.md#system-architecture-modular

Eligibility rationale:
1) DX-001 is the first item with status: todo.
2) DX-001 has no dependencies (depends_on: []).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-002+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-001 acceptance criteria:
- Single documented bootstrap command exists.
- Single documented baseline validation command exists.
- Quickstart references core governance checks.

DX-001 deliverables:
- docs/developer_quickstart.md
- Root-level command entrypoint (Makefile or equivalent)

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-001 status to done once
   acceptance criteria are met.
2) Regenerate/update next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-002 after DX-001 is done).
```

## Upcoming queue

After DX-001 is completed, the next queued item is DX-002 (depends on DX-001),
then DX-003 (depends on DX-002).
