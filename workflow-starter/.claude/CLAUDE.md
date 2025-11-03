# Claude Agent Factory - Project Instructions

**Version:** Phase 2 Complete
**Last Updated:** 2025-10-24

## Mission

A deterministic, agent-based workflow for building software with Claude Code. Transform feature requests into production-ready code through systematic planning, parallel documentation, implementation, testing, and validation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Planning (PPBV: Plan → Parallel-Plan → Build → V) │
├─────────────────────────────────────────────────────────────┤
│  /plan → planner → framework-scout → requirements-author    │
│          → test-engineer → FEAT-XXX docs created            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Implementation & Testing                          │
├─────────────────────────────────────────────────────────────┤
│  /build → implementer → code + tests written                │
│  /test → tester → validation & coverage                     │
│  /commit → git workflow → PR creation                       │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Planning Only (No Code Modification)

### Default Planning Flow

When user requests a feature:

1. **Delegate to `planner`** → `docs/features/FEAT-XXX/prd.md`
   - Extract user intent and create Product Requirements Doc
   - Define success criteria and constraints
   - Identify stakeholders and dependencies

2. **Delegate to `framework-scout`** → `docs/features/FEAT-XXX/research.md`
   - Research technical approaches and frameworks
   - Evaluate alternatives and trade-offs
   - Recommend optimal architecture patterns

3. **Delegate to `requirements-author`** → `docs/features/FEAT-XXX/architecture.md` + `docs/features/FEAT-XXX/acceptance.md`
   - Design detailed architecture and component structure
   - Write acceptance criteria (append to `/AC.md`)
   - Define interfaces and data models

4. **Delegate to `test-engineer`** → `docs/features/FEAT-XXX/testing.md` + `docs/features/FEAT-XXX/manual-test.md`
   - Create comprehensive test strategy
   - Write test stubs (failing tests)
   - Define manual testing procedures

### Phase 1 Guardrails

**CRITICAL RULES:**
- ✅ Write ONLY to `docs/features/FEAT-XXX/**` and `/AC.md`
- ❌ NEVER modify application code
- ❌ NEVER write to `src/`, `lib/`, or any code directories
- ✅ If sub-agent produces incomplete docs, ask it to fix and re-write
- ✅ Reject any write outside authorized paths

### Phase 1 Slash Commands

- `/plan <feature>` - Start planning workflow for new feature
- `/explore <topic>` - Research topic with framework-scout
- `/update-docs` - Regenerate documentation index

### Phase 1 Hooks

- **PreCompact** - Save session state before context compaction
  - Scans active features
  - Tracks recent doc changes
  - Enables context recovery

## Phase 2: Implementation & Testing (Code Modification)

### Implementation Workflow

```
/build FEAT-XXX → Implementer creates code from planning docs
                → PostToolUse hook auto-formats code
                → Test stubs become functional tests

/test FEAT-XXX  → Tester runs test suite
                → Validates against acceptance criteria
                → Generates coverage reports

/commit "msg"   → Git workflow with validation
                → Tests must pass first
                → Conventional commit format
                → Optional PR creation
                → Stop hook suggests next steps
```

### Phase 2 Slash Commands

- `/build [FEAT-XXX]` - Implement feature from planning docs
  - Read all planning artifacts
  - Follow TDD: Red → Green → Refactor
  - Respect architecture decisions
  - Generate code per SOP standards

- `/test [scope]` - Run test suite
  - `unit` - Unit tests only
  - `integration` - Integration tests
  - `e2e` - End-to-end tests
  - `all` - Full test suite (default)
  - Validate acceptance criteria
  - Generate coverage reports

- `/commit [message]` - Create git commit
  - Validate tests pass
  - Check for secrets
  - Generate conventional commit message
  - Auto-detect scope from file paths
  - Stage files and create commit
  - Optionally create PR via `gh` CLI

### Phase 2 Hooks

**PostToolUse Hook**
- Runs after `Edit` or `Write` tool usage
- Auto-formats code based on file extension:
  - JavaScript/TypeScript → `prettier`
  - Python → `black`
  - Rust → `rustfmt`
  - Go → `gofmt`
  - Ruby → `rubocop`
  - Java → `google-java-format`
- Updates docs index when docs change
- Gracefully handles missing formatters

**Stop Hook**
- Runs when agent finishes responding
- Shows git status and changed files
- Drafts conventional commit message
- Detects commit type (feat/fix/docs/test) from files
- Extracts FEAT-XXX scope from file paths
- Suggests next action (/test or /commit)

## Conventional Commits

All commits follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Commit Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Test changes
- `refactor` - Code refactoring
- `style` - Formatting
- `chore` - Tooling/config
- `perf` - Performance
- `ci` - CI/CD changes

### Scope Detection

Automatically detected from changed files:
- `docs/features/FEAT-123/**` → `FEAT-123`
- `src/auth/**` → `auth`
- `.claude/**` → `tooling`
- `docs/**` → `docs`

## Test-Driven Development

Phase 2 completes the TDD cycle started in Phase 1:

```
Phase 1: test-engineer creates test stubs (non-functional)
         ↓
Phase 2: /build makes tests functional
         → Run tests (Red - they should fail)
         → Write minimal code (Green - tests pass)
         → Refactor while tests stay green
         → Validate acceptance criteria
```

## Sub-Agent Responsibilities

### Phase 1 Agents

**planner** (`.claude/subagents/planner.md`)
- Creates Product Requirements Document
- Extracts user intent and constraints
- Writes to: `docs/features/FEAT-XXX/prd.md`

**framework-scout** (`.claude/subagents/framework-scout.md`)
- Researches technical approaches
- Evaluates alternatives and trade-offs
- Writes to: `docs/features/FEAT-XXX/research.md`

**requirements-author** (`.claude/subagents/requirements-author.md`)
- Designs architecture and components
- Creates acceptance criteria
- Writes to: `docs/features/FEAT-XXX/architecture.md`, `docs/features/FEAT-XXX/acceptance.md`, `/AC.md`

**test-engineer** (`.claude/subagents/test-engineer.md`)
- Creates test strategy
- Writes test stubs (failing tests)
- Writes to: `docs/features/FEAT-XXX/testing.md`, `docs/features/FEAT-XXX/manual-test.md`

### Phase 2 Agents

**implementer** (`.claude/subagents/implementer.md`)
- Transforms planning docs into working code
- Follows TDD practices
- Respects architecture decisions
- Writes to: application code directories

**tester** (`.claude/subagents/tester.md`)
- Executes test suites
- Validates acceptance criteria
- Generates coverage reports
- Writes to: test output and reports

## Documentation Structure

```
docs/
├── features/
│   └── FEAT-XXX_<name>/
│       ├── prd.md           # Product Requirements (planner)
│       ├── research.md      # Technical Research (framework-scout)
│       ├── architecture.md  # Architecture Design (requirements-author)
│       ├── acceptance.md    # Acceptance Criteria (requirements-author)
│       ├── testing.md       # Test Strategy (test-engineer)
│       └── manual-test.md   # Manual Test Procedures (test-engineer)
├── sop/                     # Standard Operating Procedures
├── system/                  # System-wide documentation
└── templates/               # Document templates

/AC.md                       # Acceptance Criteria (append-only)
```

## Workflow Examples

### Planning a New Feature

```
User: /plan "Add OAuth2 authentication"

Parent: Delegating to planner...
        → planner creates FEAT-042/prd.md

        Delegating to framework-scout...
        → framework-scout creates FEAT-042/research.md

        Delegating to requirements-author...
        → requirements-author creates FEAT-042/architecture.md
        → requirements-author creates FEAT-042/acceptance.md
        → Appends to /AC.md

        Delegating to test-engineer...
        → test-engineer creates FEAT-042/testing.md
        → test-engineer creates FEAT-042/manual-test.md

        Planning complete! Ready for implementation.
```

### Building a Feature

```
User: /build FEAT-042

Parent: Reading planning docs...
        → prd.md, research.md, architecture.md, testing.md

        Delegating to implementer...
        → implementer writes code following architecture
        → PostToolUse hook auto-formats code
        → Test stubs become functional tests

        Implementation complete!
        → Stop hook shows git status
        → Suggests: Run /test before committing
```

### Testing and Committing

```
User: /test FEAT-042

Parent: Delegating to tester...
        → tester runs test suite
        → All tests pass ✓
        → Coverage: 87%
        → Acceptance criteria met ✓

User: /commit "Add OAuth2 authentication"

Parent: Running validations...
        → Tests pass ✓
        → No secrets detected ✓
        → Detected: feat(FEAT-042)
        → Generated commit message

        Commit created successfully!
        → Stop hook suggests: Create PR with /pr
```

## Phase Roadmap

### Phase 1 (Complete) ✓
- [x] Parent orchestrator
- [x] Planning sub-agents (planner, framework-scout, requirements-author, test-engineer)
- [x] Planning slash commands (/plan, /explore, /update-docs)
- [x] PreCompact hook for session recovery
- [x] Documentation structure and templates

### Phase 2 (Complete) ✓
- [x] Implementation sub-agents (implementer, tester)
- [x] Implementation slash commands (/build, /test, /commit)
- [x] PostToolUse hook for auto-formatting
- [x] Stop hook for git workflow suggestions
- [x] Full TDD cycle support
- [x] Conventional commits integration

### Phase 3 (Planned)
- [ ] Full Archon MCP integration
- [ ] Stack-specific profiles (TypeScript, Python, Rust, Go)
- [ ] Advanced hooks (PreToolUse, Notification)
- [ ] CI/CD templates
- [ ] Monitoring and metrics

## Best Practices

1. **Always Start with Planning** - Run `/plan` before coding
2. **Follow TDD** - Write tests first, make them pass, refactor
3. **Commit Often** - Small, focused commits with clear messages
4. **Review Planning Docs** - Ensure alignment before implementation
5. **Validate Tests Pass** - Never commit with failing tests
6. **Use Feature Branches** - Work on branches, not main
7. **Conventional Commits** - Follow the format for clear history
8. **Trust the Process** - Let agents do their specialized work

## Error Handling

### Missing Required Section
```
Parent: ⚠️ requirements-author produced incomplete architecture.md
        Missing required section: "Component Diagram"

        Re-requesting from requirements-author...
```

### Unauthorized Write Attempt
```
Parent: ❌ Sub-agent attempted to write to src/auth.ts
        Phase 1 agents may only write to docs/** and /AC.md

        Request rejected. Aborting workflow.
```

### Test Validation Failure
```
/commit: ⚠️ Tests failed! Cannot commit with failing tests.

         Run /test to see details, or use --no-test to skip validation.
```

## Configuration

### Hooks Configuration
See `.claude/settings.json` for hook configuration.

All hooks are Python 3 scripts that:
- Accept JSON input via stdin
- Output JSON results via stdout
- Exit 0 to allow continuation
- Never block main workflow

### Sub-Agent Configuration
See `.claude/subagents/*.md` for individual agent instructions.

Each agent is a specialized Claude instance with:
- Clear mission and scope
- Defined input/output formats
- Quality standards and limits
- Template adherence requirements

## See Also

- `/docs/README.md` - Complete documentation index
- `/docs/future-enhancements.md` - Phase 3 roadmap
- `/docs/sop/` - Standard Operating Procedures
- `/.claude/commands/` - Slash command definitions
- `/.claude/hooks/` - Hook implementations
- `/.claude/subagents/` - Sub-agent instructions

---

**Remember:** Phase 1 plans, Phase 2 builds. Never modify code during planning phase. Always validate before committing. Trust the systematic workflow.
