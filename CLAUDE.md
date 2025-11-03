# AI Workflow Starter - Claude Code Configuration

## Mission

This project uses AI agents and structured workflows to take feature ideas from concept through comprehensive planning documentation, following best practices for context engineering and test-driven development.

## Project Overview

**Current Phase:** Phase 1 - Planning & Documentation
**Template Version:** 1.0.0
**Status:** Production Ready

This is a reusable template for AI-assisted software development. Clone this repository to start any new project with structured workflows, specialized agents, and automated documentation.

## Core Principles

1. **Structured Planning First:** Every feature goes through exploration → research → planning before implementation
2. **Documentation as Code:** All decisions, architecture, and acceptance criteria are documented and version-controlled
3. **Test-Driven Ready:** Test strategies and stubs created during planning, implementation follows
4. **Context Efficiency:** Just-in-time loading, minimal memory footprint, agent specialization
5. **Progressive Enhancement:** Works standalone, enhanced by optional MCPs (Archon, etc.)

## Agent System

This project uses 5 specialized sub-agents for planning and documentation, plus the main Claude Code agent for implementation (Phase 2).

### Active Sub-Agents (Phase 1)

@.claude/subagents/explorer.md
@.claude/subagents/researcher.md
@.claude/subagents/planner.md
@.claude/subagents/documenter.md
@.claude/subagents/reviewer.md

**Note:** Sub-agents focus on planning, research, and documentation. The main Claude Code agent handles all code implementation, guided by planning documents created by sub-agents.

## Workflow Commands

Use these slash commands to orchestrate multi-agent workflows:

- `/explore [topic]` - Explore new feature idea, create initial PRD
- `/plan [FEAT-ID]` - Create comprehensive planning documentation
- `/update-docs` - Maintain documentation index and cross-references

*Phase 2 commands: `/build`, `/test`, `/commit` (coming soon)*

## Documentation Structure

All documentation lives in `docs/` with automatic indexing:

- **docs/templates/** - Document templates for agents to follow
- **docs/system/** - Technical architecture (architecture, database, API, integrations, stack)
- **docs/sop/** - Standard Operating Procedures (git workflow, testing, code style, lessons learned)
- **docs/features/** - Feature-specific docs (one folder per feature: FEAT-XXX/)
- **docs/archive/** - Completed or deprecated documentation

**Key files:**
- `docs/README.md` - Auto-updated index of all documentation
- `AC.md` - Global acceptance criteria (append-only)
- `CHANGELOG.md` - Conventional changelog (auto-updated)

## Development Workflow (Phase 1)

```
User has feature idea
  ↓
/explore [topic]
  ↓ Explorer agent asks clarifying questions
  ↓ Researcher agent conducts research (optional Archon, WebSearch)
  ↓ Creates docs/features/FEAT-XXX/prd.md and research.md
  ↓
User reviews and refines PRD
  ↓
/plan FEAT-XXX
  ↓ Planner agent orchestrates planning workflow
  ↓ Creates architecture.md, acceptance.md, testing.md, manual-test.md
  ↓ Generates test stubs in tests/ directory
  ↓ Appends acceptance criteria to AC.md
  ↓ Reviewer agent validates completeness
  ↓
/update-docs
  ↓ Documenter agent updates docs/README.md index
  ↓ Updates CHANGELOG.md with planning entry
  ↓
Ready for Phase 2 implementation
```

## Test-Driven Development Approach

Phase 1 prepares for TDD:
1. **Test Strategy:** Documented in `docs/features/FEAT-XXX/testing.md`
2. **Test Stubs:** Empty test functions created in `tests/` with TODO comments
3. **Acceptance Criteria:** Clear pass/fail conditions in `AC.md`
4. **Manual Testing:** Human testing checklist in `manual-test.md`

Phase 2 will implement tests first, then code to pass them.

## Archon Integration (Optional)

This template works standalone but can be enhanced with the Archon MCP for knowledge management.

### If Archon MCP is Available:

**Researcher Agent Benefits:**
- Query pre-crawled framework documentation via `mcp__archon__search`
- Faster research with cached knowledge base
- Consistent technical context across sessions

**To Enable Archon:**
1. Install and configure Archon MCP in Claude Code settings
2. Crawl relevant framework docs to Archon knowledge base
3. Researcher agent will automatically detect and use Archon
4. Falls back to WebSearch if Archon unavailable

**Future Archon Features (Phase 3):**
- Task synchronization via `mcp__archon__tasks`
- Session state persistence via `mcp__archon__memory`
- Collaborative knowledge building

### Without Archon:

Researcher agent uses WebSearch exclusively - fully functional workflow.

## Context Management

### Memory Hierarchy
1. **CLAUDE.md** (this file) - Core orchestration, agent imports
2. **Subagents** - Specialized agent instructions (@imported above)
3. **Documentation** - JIT loading via Read tool when needed
4. **SOPs** - Referenced by agents for standards enforcement

### Session Recovery
The PreCompact hook (`.claude/hooks/pre_compact.py`) automatically saves session state before context compaction, including:
- Current feature being worked on
- Last agent invoked
- Pending tasks
- Links to key files

## Quality Gates

Every workflow includes validation:

1. **Reviewer Agent:** Validates all required sections exist
2. **Template Compliance:** Docs follow templates in `docs/templates/`
3. **SOP Enforcement:** Agents follow procedures in `docs/sop/`
4. **Completeness Checks:** No TODOs left in planning docs

## Standard Operating Procedures

Agents enforce SOPs documented in `docs/sop/`:
- **git-workflow.md** - Branching, commits, PRs
- **testing-strategy.md** - How we test
- **code-style.md** - Linting, formatting
- **mistakes.md** - Lessons learned, gotchas
- **github-setup.md** - Repository setup

## Project Customization

### For New Projects:
1. Clone this repository
2. Update this CLAUDE.md with project-specific details
3. Customize `docs/system/` with your architecture
4. Add project-specific SOPs to `docs/sop/`
5. Run `/explore` with your first feature

### Stack-Specific Profiles:
This template is generic. For stack-specific enhancements (TypeScript/React, Python/FastAPI, etc.), see `docs/future-enhancements.md`.

## Phase Roadmap

**Phase 1 (Current):** Planning & Documentation ✅
- Feature exploration and research
- Comprehensive planning documentation
- Test strategy and stubs
- Documentation maintenance

**Phase 2 (Next):** Implementation & Testing
- Main Claude Code agent implements features based on planning docs
- Test-first implementation (TDD Red-Green-Refactor cycle)
- Automated formatting and linting hooks
- Git workflow automation via slash commands

**Phase 3 (Future):** Automation & Profiles
- Full Archon integration
- Stack-specific profiles
- CI/CD integration
- Advanced hooks and automation

## Rules & Guardrails

1. **Phase 1 Agents:** Write ONLY to `docs/**`, `tests/**` (stubs only), and `AC.md`
2. **No Implementation:** Phase 1 agents must not write implementation code
3. **Template Compliance:** All feature docs must follow templates in `docs/templates/`
4. **Quality Gates:** Reviewer agent must validate before workflow completes
5. **Documentation Sync:** Documenter agent maintains docs/README.md index
6. **SOP Enforcement:** Agents must reference and follow SOPs

## Getting Help

- **Template Documentation:** See `docs/README.md` for complete documentation index
- **Workflow Examples:** See `docs/features/FEAT-001_example/` for sample workflow
- **Future Features:** See `docs/future-enhancements.md` for roadmap
- **Troubleshooting:** See `docs/sop/mistakes.md` for common issues

---

**Note:** This is Phase 1 (Planning & Documentation). Implementation agents, git automation, and advanced hooks come in Phase 2.
