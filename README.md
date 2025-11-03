# AI Workflow Starter

**A production-ready template for AI-assisted software development with structured workflows, specialized agents, and automated documentation.**

Version: 1.0.0 | Phase: 1 - Planning & Documentation | License: MIT

---

## 🎯 What Is This?

A Claude Code project template that transforms feature ideas into comprehensive planning documentation through structured AI agent workflows. Built on Anthropic's best practices for context engineering and test-driven development.

**Perfect for:**
- Solo developers building new projects
- Teams adopting AI-assisted development
- Anyone wanting structured, documented development workflows
- Projects requiring comprehensive planning before implementation

## ✨ Features

### Phase 1 (Current)
- ✅ **Structured Exploration:** `/explore` command guides feature discovery
- ✅ **Automated Research:** AI researches best practices and frameworks
- ✅ **Comprehensive Planning:** `/plan` creates architecture, acceptance criteria, and test strategy
- ✅ **Documentation Maintenance:** Auto-generated indexes and changelogs
- ✅ **5 Specialized Agents:** Explorer, Researcher, Planner, Documenter, Reviewer
- ✅ **Session Recovery:** PreCompact hook saves state before context compaction
- ✅ **Test-Ready:** Generates test stubs following TDD principles

### Phase 2 (Coming Soon)
- ⏳ Implementation agents with TDD workflow
- ⏳ Automated testing and validation
- ⏳ Git workflow automation
- ⏳ Code formatting hooks

### Phase 3 (Future)
- ⏳ Full Archon MCP integration
- ⏳ Stack-specific profiles (TypeScript/React, Python/FastAPI, Rust)
- ⏳ CI/CD templates
- ⏳ Advanced automation

## 🚀 Quick Start

Choose your path: Starting a **new project** from scratch, or adding this workflow to an **existing project**.

---

### Path A: New Project from Scratch

**Best for:** Greenfield projects, prototypes, or learning the workflow

#### 1. Clone This Template

```bash
git clone https://github.com/your-username/ai-workflow-starter.git my-new-project
cd my-new-project
```

#### 2. Clean Git History (Optional)

```bash
# Start with fresh commit history
rm -rf .git
git init
git add .
git commit -m "init: AI workflow starter template"
```

#### 3. Customize Project Context

```bash
# Update CLAUDE.md:
# - Change project name and description
# - Update tech stack in "Project Context" section
# - Adjust agent tools if needed

# Update docs/system/ files:
# - architecture.md: Your system design
# - database.md: Your data model
# - stack.md: Your technologies
# - integrations.md: Your external services
# - api.md: Your API design (if applicable)
```

#### 4. Configure Your Environment

```bash
# If using Archon MCP (optional):
# - Install Archon MCP
# - Configure in Claude Code settings
# - Researcher agent will automatically use it

# Otherwise, agents fall back to WebSearch (works perfectly fine)
```

#### 5. Start Your First Feature

```bash
# In Claude Code, run:
/explore user authentication

# The Explorer agent will:
# - Search your codebase for existing patterns
# - Ask clarifying questions
# - Create a comprehensive PRD

# Then plan the feature:
/plan FEAT-001

# The Planner will:
# - Create architecture decision document
# - Generate acceptance criteria
# - Create testing strategy
# - Generate test stubs
# - Validate everything with Reviewer
```

#### 6. Review & Iterate

```bash
# Review all planning docs in docs/features/FEAT-001_[feature]/
# If changes needed, refine and re-run /plan FEAT-001
# When ready, use the main Claude Code agent to implement (Phase 2)
```

---

### Path B: Add to Existing Project

**Best for:** Mature projects that want structured planning workflows

#### 1. Selective File Copy

**Don't clone the entire repo.** Instead, selectively copy these components:

```bash
# Core workflow files (REQUIRED)
cp -r /path/to/template/.claude your-project/
cp /path/to/template/AC.md your-project/
cp /path/to/template/CHANGELOG.md your-project/

# Documentation structure (RECOMMENDED)
cp -r /path/to/template/docs/templates your-project/docs/
cp -r /path/to/template/docs/sop your-project/docs/
mkdir -p your-project/docs/features
mkdir -p your-project/docs/system

# System docs as examples (OPTIONAL)
# Only if you don't have these already
cp /path/to/template/docs/system/* your-project/docs/system/
```

#### 2. Integrate CLAUDE.md

**Option A: Merge into Existing CLAUDE.md**
If you already have a CLAUDE.md file:
```bash
# Copy the agent imports section:
@.claude/subagents/*.md

# Copy the workflow command sections:
## Feature Exploration Workflow: /explore
## Planning Workflow: /plan
## Documentation Maintenance: /update-docs

# Adjust to fit your existing structure
```

**Option B: Replace CLAUDE.md**
If you don't have a CLAUDE.md or want to start fresh:
```bash
cp /path/to/template/CLAUDE.md your-project/
# Then customize the "Project Context" section
```

#### 3. Baseline Existing Features

Document your existing features to establish a baseline:

```bash
# In Claude Code:
"Please help me baseline my existing features. Scan the codebase and create
stub documentation in docs/features/ for major existing features. Just create
basic PRD entries noting they're already implemented."

# This gives you:
# - FEAT-001_existing_auth/ with basic PRD
# - FEAT-002_existing_dashboard/ with basic PRD
# - etc.

# Mark them as "Status: Implemented (baseline)"
```

#### 4. Update System Documentation

```bash
# Update docs/system/ files with your ACTUAL architecture:
# - architecture.md: Your current system design
# - database.md: Your current schema
# - stack.md: Your actual tech stack
# - integrations.md: Your actual external services

# This context helps agents understand your project
```

#### 5. Configure for Your Stack

```bash
# Update docs/sop/code-style.md with your linters/formatters
# Update docs/sop/testing-strategy.md with your test framework
# Update docs/sop/git-workflow.md with your branching strategy
```

#### 6. Start Your First New Feature

```bash
# Now you're ready to use the workflow for new features:
/explore new-feature-idea

# The Explorer will search your existing codebase
# The workflow will integrate with your existing patterns
```

---

### Path C: Example - Adding to a RAG Project

**Concrete example** for integrating with an existing project:

```bash
# Your existing RAG project structure:
your-rag-project/
├── src/
│   ├── embeddings/
│   ├── retrieval/
│   └── generation/
├── tests/
├── docs/
└── README.md

# Step 1: Add workflow files
cd your-rag-project
mkdir -p .claude/subagents .claude/commands .claude/hooks
mkdir -p docs/features docs/templates docs/sop docs/system

# Copy agent definitions
cp /path/to/template/.claude/subagents/*.md .claude/subagents/
cp /path/to/template/.claude/commands/*.md .claude/commands/
cp /path/to/template/.claude/hooks/*.py .claude/hooks/
cp /path/to/template/.claude/settings.json .claude/

# Copy documentation templates and SOPs
cp -r /path/to/template/docs/templates docs/
cp -r /path/to/template/docs/sop docs/

# Copy root files
cp /path/to/template/AC.md .
cp /path/to/template/CHANGELOG.md .

# Step 2: Baseline existing RAG features
# In Claude Code:
"Create baseline documentation for my existing RAG features:
1. Embedding generation (src/embeddings/)
2. Vector retrieval (src/retrieval/)
3. LLM generation (src/generation/)"

# Step 3: Document your RAG architecture
# Update docs/system/architecture.md with:
# - RAG pipeline architecture
# - Vector database choice (Pinecone/Weaviate/etc)
# - LLM providers
# - Chunking strategy

# Update docs/system/stack.md with:
# - LangChain/LlamaIndex/custom
# - Vector DB
# - LLM providers
# - Dependencies

# Step 4: Plan your first new RAG feature
/explore hybrid search with keyword + vector

# The agents now understand your RAG context and will:
# - Reference your existing embedding system
# - Consider your vector DB capabilities
# - Integrate with your LLM generation pipeline
```

---

### 🎯 Success Criteria

**You know the setup is complete when:**

✅ `/explore test-feature` successfully creates a PRD
✅ `/plan FEAT-XXX` generates all 6 planning documents
✅ `/update-docs` regenerates the documentation index
✅ Agents reference your existing codebase patterns
✅ Test stubs are created in your tests/ directory
✅ CLAUDE.md reflects your project's actual context

---

### 🆘 Troubleshooting Setup

**Problem:** Agents can't find templates
```bash
# Solution: Ensure docs/templates/ exists and has all 6 templates
ls docs/templates/
# Should show: prd-template.md, research-template.md, architecture-template.md,
#              acceptance-template.md, testing-template.md, manual-test-template.md
```

**Problem:** /explore or /plan commands not recognized
```bash
# Solution: Check .claude/commands/ exists and contains .md files
ls .claude/commands/
# Should show: explore.md, plan.md, update-docs.md
```

**Problem:** Agents make wrong assumptions about tech stack
```bash
# Solution: Update CLAUDE.md "Project Context" section with actual tech stack
# Also update docs/system/stack.md with specific versions and choices
```

**Problem:** Want to skip Archon setup
```bash
# No problem! Archon is completely optional.
# Researcher agent automatically falls back to WebSearch if Archon unavailable.
# The template works perfectly without it.
```

---

### 📝 Next Steps After Setup

```bash
# After setup, your typical workflow:
1. /explore [feature-idea]  # Create PRD + research
2. /plan FEAT-XXX          # Create planning docs + test stubs
3. [Implement via main agent]  # Write code (Phase 2)
4. /update-docs            # Keep documentation current
```

## 📖 Documentation

### For Users
- **[CLAUDE.md](CLAUDE.md)** - Full workflow documentation and agent system
- **[docs/README.md](docs/README.md)** - Complete documentation index
- **[docs/features/FEAT-001_example/](docs/features/FEAT-001_example/)** - Example feature walkthrough

### SOPs (Standard Operating Procedures)
- **[git-workflow.md](docs/sop/git-workflow.md)** - Branching, commits, PRs
- **[testing-strategy.md](docs/sop/testing-strategy.md)** - TDD approach and test levels
- **[code-style.md](docs/sop/code-style.md)** - Code quality standards
- **[mistakes.md](docs/sop/mistakes.md)** - Lessons learned log
- **[github-setup.md](docs/sop/github-setup.md)** - Repository configuration

### For Agents
- **[.claude/subagents/](. claude/subagents/)** - Agent definitions
- **[.claude/commands/](.claude/commands/)** - Slash command workflows
- **[docs/templates/](docs/templates/)** - Documentation templates

## 🛠️ Project Structure

```
ai-workflow-starter/
├── CLAUDE.md                      # Main orchestration (read this first!)
├── AC.md                          # Global acceptance criteria
├── CHANGELOG.md                   # Project changelog
├── .claude/
│   ├── subagents/                 # 7 agent definitions
│   ├── commands/                  # 6 slash commands
│   ├── hooks/                     # Automation (PreCompact + Phase 2 stubs)
│   └── settings.json              # Hook configuration
├── docs/
│   ├── templates/                 # Doc templates for agents
│   ├── system/                    # Architecture, database, API, stack
│   ├── sop/                       # Standard operating procedures
│   ├── features/                  # Feature planning docs
│   │   └── FEAT-001_example/      # Complete example
│   └── README.md                  # Documentation index (auto-updated)
└── tests/                         # Test stubs (Phase 1), implementations (Phase 2)
```

## 🎓 Workflow Example

```
1. EXPLORE
   User: /explore user dashboard
   → Explorer asks clarifying questions
   → Researcher investigates best practices
   → Creates docs/features/FEAT-002_dashboard/prd.md + research.md

2. PLAN
   User: /plan FEAT-002
   → Planner creates architecture.md (3 options, comparison, recommendation)
   → Creates acceptance.md (Given/When/Then criteria)
   → Creates testing.md (test strategy)
   → Creates manual-test.md (human testing guide)
   → Generates test stubs in tests/
   → Reviewer validates completeness
   → Documenter updates docs/README.md

3. REVIEW & REFINE
   User reviews all planning docs
   User refines requirements if needed
   Re-run /plan if changes needed

4. READY FOR PHASE 2
   Feature fully planned with:
   ✅ Complete documentation
   ✅ Architecture decision
   ✅ Acceptance criteria
   ✅ Test stubs
   ✅ Manual test guide
```

## 🤖 Available Commands

### Active (Phase 1)
- `/explore [topic]` - Research and draft feature requirements
- `/plan [FEAT-ID]` - Create comprehensive planning documentation
- `/update-docs` - Maintain documentation index and links

### Coming in Phase 2
- `/build [FEAT-ID]` - Implement feature with TDD
- `/test [FEAT-ID]` - Run tests and validate
- `/commit [message]` - Git workflow with validation

## 🎯 Design Principles

1. **Planning First:** Comprehensive documentation before implementation
2. **Test-Driven:** Test strategy and stubs before code
3. **Agent Specialization:** 7 focused agents vs. one generalist
4. **Context Efficiency:** JIT loading, minimal memory footprint
5. **Quality Gates:** Reviewer validates before completion
6. **Progressive Enhancement:** Works standalone, better with MCPs

## 🔧 Configuration

### Optional: Archon MCP

This template works standalone but can be enhanced with Archon for knowledge management:

1. Install Archon MCP (see [Archon docs](https://github.com/cyanheads/archon))
2. Configure in Claude Code settings
3. Researcher agent will automatically use it
4. Falls back to WebSearch if unavailable

### Stack Customization

Currently generic (stack-agnostic). To customize:

1. Update `docs/system/stack.md` with your technologies
2. Update `docs/system/architecture.md` with your design
3. Add stack-specific configurations as needed
4. Phase 3 will add pre-configured profiles

## 📊 Project Status

**Phase 1: Complete** ✅
- All agents, commands, and documentation in place
- Hooks configured
- Templates ready
- Example feature demonstrated

**Phase 2: Planned** ⏳
- Implementation agents
- Test execution
- Git automation
- See [docs/future-enhancements.md](docs/future-enhancements.md)

## 🤝 Contributing

This is a template repository. To contribute:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/improvement-name`
3. Follow the workflow: `/explore`, `/plan`, implement
4. Create PR with conventional commit format

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

Built on:
- [Anthropic's Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Context Engineering patterns](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Conventional Commits](https://www.conventionalcommits.org/)
- Inspired by [coleam00's workflow foundation](https://github.com/coleam00/context-engineering-intro)

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/your-username/ai-workflow-starter/issues)
- **Documentation:** [docs/README.md](docs/README.md)
- **Example:** [docs/features/FEAT-001_example/](docs/features/FEAT-001_example/)

---

**Ready to build with structured AI workflows? Start with `/explore your-feature-idea`**
