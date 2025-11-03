# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial AI Workflow Starter template v1.0.0
- Phase 1: Planning & Documentation system
- 5 specialized sub-agents (Explorer, Researcher, Planner, Documenter, Reviewer)
- 6 slash commands (3 active: /explore, /plan, /update-docs + 3 Phase 2 stubs: /build, /test, /commit)
- PreCompact hook for session state recovery
- 6 documentation templates (PRD, research, architecture, acceptance, testing, manual-test)
- 6 Standard Operating Procedures (SOPs)
- 5 system documentation files
- FEAT-001 example feature demonstrating complete workflow
- Comprehensive README and documentation index
- Test-driven development support with test stub generation
- FEAT-000: Shared Infrastructure planning complete - architecture, acceptance criteria, and testing strategy documented (2025-11-03)

### Phase Roadmap
- Phase 1 (Current): Planning & Documentation - Complete ✅
- Phase 2 (Next): Implementation workflow (main agent), testing automation, git workflow
- Phase 3 (Future): Full Archon integration, stack profiles, advanced automation

## [1.0.0] - 2025-10-24

### Added
- Initial template release
- Complete Phase 1 planning workflow
- Agent system with specialization
- Documentation automation
- Session recovery via PreCompact hook
- Quality gates with Reviewer agent
- Example feature for reference

### Documentation
- CLAUDE.md orchestration
- Complete agent definitions
- Slash command workflows
- SOP documentation
- System architecture templates
- Testing strategy
- Git workflow standards

### Infrastructure
- Directory structure
- Hook system configuration
- Template system
- Documentation index automation

---

**Note:** This changelog is automatically updated by the Documenter agent when running `/update-docs` or during feature planning. Feature-specific entries will be appended as development progresses.

**Convention:** We follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages, which feeds into this changelog.
