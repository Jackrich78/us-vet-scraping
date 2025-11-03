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
- FEAT-001: Google Maps Scraping & Notion Integration planning complete - Ready for implementation (2025-11-03)
  - 4 planning documents created (architecture, acceptance, testing, manual-test)
  - 30 acceptance criteria defined (27 Must Have, 3 Should Have)
  - 8 test stub files generated (5 unit, 2 integration, 1 e2e)
  - Architecture decision: Modular Pipeline with Apify compass/crawler-google-places actor
  - Components: ApifyClient, DataFilter, InitialScorer, NotionBatchUpserter
- FEAT-002: Website Enrichment & LLM Extraction planning complete - Ready for implementation (2025-11-03)
  - 6 planning documents created (prd, research, architecture, acceptance, testing, manual-test)
  - 43 acceptance criteria defined across functional, performance, quality, and operational requirements
  - 51 test stubs created covering unit, integration, and e2e scenarios
  - Architecture decision: Option 2 - Crawl4AI (Async) + OpenAI GPT-4o-mini + Structured Outputs
  - Components: WebsiteCrawler, LLMExtractor, EnrichmentUpdater, RateLimiter
  - 30-minute spike required to validate Crawl4AI extraction quality before full implementation
  - 3 architectural options evaluated: Firecrawl (rejected - cost), Crawl4AI (recommended), Scrapy (rejected - complexity)

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
