# Technology Stack

**Last Updated:** 2025-11-03
**Status:** Active

## Overview

This document lists all technologies, frameworks, libraries, and tools used in the US Veterinary Lead Generation System.

**Project Type:** CLI / Batch Processing Pipeline
**Phase:** Phase 1 - Planning & Documentation (Ready for Phase 2 - Implementation)

## Core Technologies

### Language

**Python**
- **Version:** 3.11+
- **Why:** Rich ecosystem for web scraping, API integration, and data processing. Excellent library support for Apify, OpenAI, and Notion APIs.
- **Use Cases:** All pipeline components - scraping, enrichment, scoring, and data push
- **Environment:** Virtual environment (venv) for dependency isolation

## Backend / Processing Pipeline

### Script Type

**Batch Processing Pipeline**
- **Execution:** Command-line script with orchestration
- **Mode:** One-time or recurring (cron-scheduled)
- **Test Support:** `--test` flag for limited 10-practice runs during development

## Database

### Primary Database

**Notion (via API)**
- **Version:** API v1 (2022-06-28)
- **Why:** Client requirement - Notion workspace already in use for sales workflow
- **Client Library:** notion-client 2.2.1
- **Schema:** 48-field database for veterinary practice leads
- **Rate Limits:** 3 requests/second
- **Batch Strategy:** 10 records per API call (conservative to stay under rate limits)

### Local Storage

**File System (JSON/CSV)**
- **Purpose:** Raw data backup and debugging
- **Structure:**
  - `data/raw/` - Raw API responses (Apify, OpenAI)
  - `data/processed/` - Transformed data before Notion push
  - `data/logs/` - Execution logs and error reports

## Core Dependencies

### Web Scraping & API Clients

**apify-client**
- **Version:** 1.7.2
- **Purpose:** Google Maps scraping, optional LinkedIn enrichment
- **Documentation:** https://docs.apify.com/api/client/python

**crawl4ai**
- **Version:** 0.3.74
- **Purpose:** Website scraping with JavaScript rendering
- **Features:** Headless browser automation, dynamic content handling
- **Documentation:** https://crawl4ai.com/docs

### AI/ML Integration

**openai**
- **Version:** 1.54.3
- **Purpose:** GPT-4o-mini for website data extraction
- **Model:** gpt-4o-mini
- **Cost:** ~$0.02 per extraction call
- **Rate Limits:** Tier-based (verified during setup)
- **Documentation:** https://platform.openai.com/docs

### Data Storage

**notion-client**
- **Version:** 2.2.1
- **Purpose:** Push/update leads in Notion database
- **API Version:** 2022-06-28
- **Documentation:** https://ramnes.github.io/notion-sdk-py

### Utilities

**python-dotenv**
- **Version:** 1.0.1
- **Purpose:** Load environment variables from .env file

**pydantic**
- **Version:** 2.9.2
- **Purpose:** Data validation and settings management
- **Use:** Config validation, API response schemas

**tenacity**
- **Version:** 9.0.0
- **Purpose:** Retry logic with exponential backoff
- **Configuration:** 3 attempts, delays: 5s, 10s, 20s

**requests**
- **Version:** 2.32.3
- **Purpose:** HTTP requests (fallback for simple API calls)

**beautifulsoup4**
- **Version:** 4.12.3
- **Purpose:** HTML parsing (supplementary to Crawl4AI)

## Testing

### Test Framework

**pytest**
- **Version:** 8.3.3
- **Purpose:** Unit and integration testing
- **Coverage:** pytest-cov for coverage reports
- **Target:** 80%+ coverage for core logic

### Test Strategy

- **Unit Tests:** Individual scrapers, scoring logic, data transformers
- **Integration Tests:** Full pipeline with test mode (10 practices)
- **Mocking:** pytest-mock for external API calls (avoid costs during testing)
- **Fixtures:** Sample Apify/LLM responses for reproducible tests

## Development Tools

### Package Manager

- **Tool:** pip
- **Version:** 24.0+
- **Lock File:** requirements.txt
- **Virtual Environment:** venv (Python standard library)

### Code Quality

**Linting:**
- **Tool:** ruff
- **Version:** 0.7.0+
- **Config:** pyproject.toml or ruff.toml
- **Rules:** Google Python Style Guide compliance

**Formatting:**
- **Tool:** black
- **Version:** 24.10.0+
- **Line Length:** 100 characters
- **Config:** pyproject.toml

**Type Checking:**
- **Tool:** Python type hints (PEP 484)
- **Enforcement:** Optional mypy for strict type checking
- **Coverage:** All public functions annotated

### Version Control

- **Git:** 2.x
- **Branch Strategy:** Feature branches (see [git-workflow.md](../sop/git-workflow.md))
- **Commit Format:** Conventional commits (feat, fix, docs, test, refactor, chore)

## Deployment

### Hosting

**Platform:** Local execution (developer machine)

**Environments:**
- **Development:** Local with --test flag (10 practices)
- **Production:** Local full run (150+ practices)
- **Future:** Cron job or cloud scheduler for recurring runs

### CI/CD

**Platform:** GitHub Actions (future enhancement)

**Planned Pipeline:**
1. Lint with ruff
2. Format check with black
3. Run pytest with coverage
4. Validate config schema

**Note:** CI/CD deferred to Phase 3 - MVP runs locally

## Monitoring & Observability

### Logging

- **Tool:** Python `logging` module (standard library)
- **Format:** Structured JSON logs
- **Levels:** DEBUG (dev), INFO (production), WARNING, ERROR, CRITICAL
- **Destinations:**
  - Console: Human-readable output with colors
  - File: `data/logs/scraper_YYYY-MM-DD_HH-MM-SS.log`
  - Rotation: Daily logs, keep last 7 days

### Error Tracking

- **Tool:** Custom error aggregation (no external service for MVP)
- **Strategy:**
  - Log all errors with context
  - Aggregate error summary at end of run
  - Email report (optional future enhancement)

### Cost Tracking

- **Strategy:** Log estimated costs per API call
- **Calculation:**
  - Apify: $0.01 per Google Maps result
  - OpenAI: $0.02 per extraction call (gpt-4o-mini)
  - Total budget: <$10 for 150 practices
- **Reporting:** Cost summary in final log output

## AI/ML Tools

### Claude Code

- **Version:** Latest (Sonnet 4.5)
- **Configuration:** [CLAUDE.md](../../CLAUDE.md), [.claude/CLAUDE.md](../../.claude/CLAUDE.md)
- **Agents:** Specialized planning and implementation agents
- **Commands:** `/plan`, `/build`, `/test`, `/commit`, `/prime`, `/explore`
- **Purpose:** AI-assisted development workflow

### MCPs (Model Context Protocol)

**Archon MCP**
- **Status:** Available
- **Purpose:** Knowledge management, web research, task tracking
- **Use:** Research phase for technical approaches and documentation

## Development Setup

### Prerequisites

```bash
# Python version
python3 --version  # 3.11+

# pip version
pip --version  # 24.0+

# Playwright (for Crawl4AI)
playwright install
```

### Installation

```bash
# Clone repository
git clone https://github.com/username/us_vet_scraping.git
cd us_vet_scraping

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys:
#   APIFY_API_KEY=your_apify_key
#   OPENAI_API_KEY=your_openai_key
#   NOTION_API_KEY=your_notion_key
#   NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744

# Validate configuration
python -m src.utils.config_loader --validate

# Run in test mode (10 practices)
python main.py --config config/config.json --test

# Run full pipeline
python main.py --config config/config.json
```

## Performance Considerations

### Execution Time

- **Google Maps Scraping:** ~5 minutes for 150-200 practices (Apify actor speed)
- **Website Enrichment:** ~1.5 hours for 150 practices (3-5s per site * 150 = 450-750s + LLM calls)
- **Scoring:** < 1 minute (local computation)
- **Notion Push:** ~1 minute (batched API calls)
- **Total MVP Run:** ~2 hours end-to-end

### Rate Limiting

- **Apify:** No strict limits (usage-based billing)
- **OpenAI:** Tier-based (verify account tier before full run)
- **Notion:** 3 req/s → use 10 records per call, 0.3s delay between calls
- **Website Scraping:** 3-5s delay between requests (respectful scraping)

## Security

### Dependencies

- **Audit Tool:** `pip-audit` or `safety check`
- **Automation:** GitHub Dependabot (future)
- **Policy:** Review and update dependencies monthly

### Secrets Management

- **Tool:** Environment variables via python-dotenv
- **Storage:** `.env` file (gitignored)
- **Production:** Environment variables in CI/CD or cloud scheduler
- **Never commit:** API keys, tokens, database IDs

### API Key Permissions

- **Apify:** Read/Execute actors only (no write access to account)
- **OpenAI:** API key (not organization admin)
- **Notion:** Integration with specific database access only (not workspace admin)

## Documentation

### Code Documentation

- **Style:** Google Python docstrings
- **Coverage:** All public functions, classes, and modules
- **Example:**
  ```python
  def calculate_lead_score(practice: Practice) -> int:
      """Calculate ICP fit score for a veterinary practice.

      Args:
          practice: Practice object with enriched data

      Returns:
          Score from 0-120 based on ICP fit criteria
      """
  ```

### Project Documentation

- **Location:** `docs/` directory
- **Structure:** System docs, SOPs, feature docs, templates
- **Maintenance:** Update with `/ update-docs` command

## Tech Debt Tracking

*Document known technical debt (MVP intentional shortcuts)*

- **No email verification:** Pattern guessing only (Phase 2: SMTP verification)
- **No proxy rotation:** Relying on Crawl4AI defaults (Phase 2: Add if blocking occurs)
- **No recurring de-duplication:** One-time scrape (Phase 2: FEAT-005)
- **Manual Notion schema setup:** No automated schema validation (Phase 2: Add Pydantic validation)
- **Local execution only:** No cloud deployment (Phase 3: Cloud scheduler)

## Alternative Technologies Considered

| Technology | Considered For | Why Not Chosen |
|------------|----------------|----------------|
| Scrapy | Website scraping | Crawl4AI better for JavaScript-heavy sites |
| Claude API directly | LLM extraction | OpenAI GPT-4o-mini more cost-effective ($0.02 vs $0.15 per call) |
| Airtable | Lead database | Client already uses Notion |
| BeautifulSoup only | Web scraping | Doesn't handle JavaScript rendering (Crawl4AI does) |
| Selenium | Browser automation | Crawl4AI built on Playwright (faster, more reliable) |
| Langchain | LLM orchestration | Over-engineered for simple extraction task |

---

**Note:** Update this document when:
- New technologies are adopted
- Versions are upgraded
- Tools are replaced
- Stack recommendations change

**See Also:**
- [architecture.md](architecture.md) - System architecture
- [integrations.md](integrations.md) - External services
- [docs/sop/code-style.md](../sop/code-style.md) - Code standards
