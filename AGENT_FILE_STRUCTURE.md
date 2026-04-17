# Recommended File Structure (Codex + Claude Code)

Use this as a practical, repository-level layout to operate both agents consistently.

```text
pressure_vessels/
├─ README.md
├─ AGENT_GOVERNANCE.md                 # policy, risk gates, approvals, audit rules
├─ AGENT_FILE_STRUCTURE.md             # this file
├─ .agents/
│  ├─ shared/
│  │  ├─ standards.md                  # shared coding and review standards
│  │  ├─ risk-matrix.md                # low/medium/high examples for this repo
│  │  └─ pr-checklist.md               # reusable checklist text for PRs
│  ├─ codex/
│  │  ├─ AGENTS.md                     # Codex execution rules in this repo
│  │  ├─ playbook.md                   # Codex workflow (plan->implement->test)
│  │  └─ prompts/
│  │     ├─ feature.md                 # feature implementation prompt template
│  │     ├─ bugfix.md                  # bugfix prompt template
│  │     └─ refactor.md                # refactor prompt template
│  └─ claude/
│     ├─ CLAUDE.md                     # Claude Code execution/review rules
│     ├─ playbook.md                   # Claude workflow (analyze->review->harden)
│     └─ prompts/
│        ├─ review.md                  # adversarial review template
│        ├─ security.md                # security review template
│        └─ test-gaps.md               # missing-tests review template
├─ .github/
│  ├─ pull_request_template.md         # includes governance checklist
│  └─ workflows/
│     ├─ ci.yml                        # lint/test/build checks
│     └─ agent-governance.yml          # verify checklist/risk label presence
└─ docs/
   ├─ architecture.md
   ├─ decision-log/
   │  └─ ADR-0001-agent-governance.md
   └─ incidents/
      └─ TEMPLATE.md
```

---

## Why this structure works

- **Clear separation**: each agent has a dedicated folder for instructions and prompts.
- **Shared baseline**: common standards and risk matrix stay in `.agents/shared/`.
- **Operational enforcement**: `.github/` keeps governance close to CI/PR controls.
- **Auditability**: `docs/decision-log` and `docs/incidents` create a durable record.

---

## Minimum viable subset (start here)

If you want the smallest possible setup first, create only:

1. `AGENT_GOVERNANCE.md`
2. `.agents/codex/AGENTS.md`
3. `.agents/claude/CLAUDE.md`
4. `.github/pull_request_template.md`

Then add CI and prompt libraries as the team matures.
