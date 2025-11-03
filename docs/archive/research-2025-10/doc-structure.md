# Notes - Documentation Structure

## Core Structure Identified

### Folder System:

- **`.agent/`** (or user prefers `/doc`?) containing:
    - `system/` - Architecture, DB schema, APIs, integrations
    - `SOP/` - Standard Operating Procedures, mistakes learned
    - `features/` (or `tasks/`?) - PRDs with acceptance criteria
    - `commands/` - Slash command specifications
    - `README.md` - Index of all docs

### Root-Level Docs (currently outside `.agent/`):

- `claude.md` - Prime directives, project rules
- `spec.md` - Evolving spec
- `AC.md` - Acceptance criteria (Given/When/Then)
- `progress.md` - Terse run logs
- `decisions.md` - ADRs (Architecture Decision Records)
- `bugs.md` - Bug tracker
- `CHANGELOG.md` - Release notes
- `README.md` - Repo overview

## Key Command: `/update-doc`

**Three modes:**

- `init` - Bootstrap documentation system
- `update [scope] [note]` - Refresh docs after changes
- `new <type> <title>` - Create new doc skeleton

**Guardrails:**

- No duplication (single source of truth)
- TODO for unknowns, never guess
- Keep docs ≤800-1200 words
- Update index + cross-links always
- Write changelog/progress entries

## Sub-agents/Skills Mentioned:

- `/research` → Research skill (writes research.md)
- `/spec` → Spec author (updates spec.md)
- `/tests` → Test author (writes AC.md)
- `/impl` → Implementer (code changes)
- `/update-doc` → Docs updater (the focus here)
- `/commit` → Git preflight

## Archon Integration Proposed:

- **Read-only for v0.1:** `docs.search`, `docs.fetch`, `tasks.list`
- **Write operations:** Behind `/approve` gates
- Mistake → SOP loop via Archon task creation (gated)

---

## 🚨 Critical Questions & Conflicts to Resolve:

### 1. **Folder Location:**

- Document uses `.agent/` folder
- You want "all documentation live within a `/doc` folder"
- **Question:** Is `/doc` just a naming preference, or should ALL docs (including claude.md, spec.md, etc.) live inside it?

### 2. **Root-Level Files:**

- The structure has many files at root (claude.md, spec.md, AC.md, progress.md, decisions.md, bugs.md)
- **Question:** Should these move into `/doc` too, or stay at root for easy access?

### 3. **Complexity Management:**

- This system has 8+ root files + 4 subdirectories + multiple commands
- You emphasized "don't want to make this overly complex from the beginning"
- **Question:** What's the absolute minimum for v0.1? Can we phase in features?

### 4. **Sub-agent Implementation:**

- Document assumes "Claude Skills" for sub-agents
- You mentioned "libraries around that I want to try and use"
- **Question:** Are you using Claude Skills exclusively, or other frameworks (PydanticAI, LangGraph, custom scripts)?

### 5. **Features vs. Tasks:**

- Document says `features/` folder (but mentions "rename to tasks if you prefer")
- Archon uses "tasks"
- **Question:** Should we stick with "tasks" for consistency with Archon?

### 6. **Archon Write Access:**

- Document suggests read-only Archon for v0.1
- You want Archon as "agent memory and project planning"
- **Question:** Should Archon be able to write tasks immediately, or keep it read-only initially?

### 7. **Git Automation:**

- Document has `/commit` command with manual approval gates
- You want "instructions to push to Git"
- **Question:** How automated should Git operations be? Manual steps vs. automated commits?

### 8. **Slash Commands vs. Sub-agents:**

- Are slash commands just *triggers* for sub-agents?
- Or are they standalone prompts/scripts?
- **Question:** How are slash commands implemented technically?

---

## What I Strongly Like (Recommend Keeping):

✅ **SOP/System/Features structure** - Clear separation of concerns

✅ **`/update-doc` command** - Maintains doc consistency automatically

✅ **Guardrails** (no duplication, TODO for unknowns, bounded scope)

✅ **Index-based navigation** (README as entry point)

✅ **Progress tracking** (progress.md + CHANGELOG.md)

✅ **Acceptance checks** (done = all checks pass)

## What Needs Clarification Before Adopting:

⚠️ Folder naming and organization

⚠️ Minimum viable version (what can wait?)

⚠️ Sub-agent technology choices

⚠️ Archon integration depth

⚠️ Git workflow automation level

⚠️ Terminology consistency (features vs. tasks)