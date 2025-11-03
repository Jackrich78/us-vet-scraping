# Veterinary Practice Lead Generation & Scoring System

**Version:** 1.0 MVP
**Target Market:** Boston, MA Veterinary Clinics
**Objective:** Generate 150+ scored, enriched leads ready for cold calling

---

## 🎯 Overview

Automated lead generation pipeline that scrapes Google Maps, enriches with website data, scores ICP fit (0-120 points), and pushes qualified leads to Notion for sales workflow.

**Key Features:**
- 🗺️ Google Maps scraping (Apify)
- 🌐 Website enrichment (Crawl4AI + OpenAI GPT-4o-mini)
- 📊 ICP fit scoring (0-120 point algorithm)
- 📝 Notion integration (batch upsert with de-duplication)
- 🎯 Decision maker identification
- 💡 Personalization context extraction

**Target ICP:** 3-5 veterinarian practices (multi-vet, not too corporate)

---

## 📈 Success Metrics

- ✅ 150+ practices in Notion database
- ✅ 95%+ have confirmed vet count
- ✅ 60%+ have identified decision maker name
- ✅ 50%+ have personalization context for outreach
- ✅ All leads scored and prioritized (Hot/Warm/Cold/Out of Scope)
- ✅ Total cost ≤$1.10 (Apify $0.90 + OpenAI $0.10)
- ✅ Total runtime ≤16 minutes

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│ FEAT-000: Shared Infrastructure                        │
│ • ConfigLoader (Pydantic v2 validation)                │
│ • Logger (dual JSON + colorized console)               │
│ • RetryHandler (Tenacity exponential backoff)          │
│ • NotionClient (rate limiting, batch upsert)           │
│ • ErrorTracker (aggregated error reporting)            │
│ • Pydantic Models (type-safe data schemas)             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ FEAT-001: Google Maps Scraping & Notion Push           │
│ • Apify compass/crawler-google-places actor            │
│ • Hard filters (has website, 10+ reviews, not closed)  │
│ • Initial scoring (0-25 points baseline)               │
│ • Batch upsert to Notion (de-dup by Place ID)         │
│ Output: ~150 practices, ~8 minutes                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ FEAT-002: Website Enrichment & LLM Extraction          │
│ • Crawl4AI async scraping (5 concurrent tabs)          │
│ • OpenAI GPT-4o-mini structured outputs                │
│ • Extract: vet count, decision makers, services, tech  │
│ • Update Notion with enrichment data                   │
│ Output: ~145 enriched practices, ~7.65 minutes         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ FEAT-003: ICP Fit Lead Scoring & Prioritization        │
│ • Practice size score (0-40 pts)                       │
│ • Call volume indicators (0-30 pts)                    │
│ • Technology adoption (0-20 pts)                       │
│ • Baseline score (0-10 pts)                            │
│ • Decision maker bonus (0-20 pts)                      │
│ • Classify: Solo/Small/Sweet Spot/Large/Corporate      │
│ • Prioritize: Hot/Warm/Cold/Out of Scope               │
│ Output: All practices scored, ~0.9 minutes             │
└─────────────────────────────────────────────────────────┘
```

**Total Pipeline Runtime:** ~16 minutes (Apify 8 min + Scraping 7.65 min + Scoring 0.9 min)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Apify API key ([get free tier](https://apify.com))
- OpenAI API key ([get API key](https://platform.openai.com/api-keys))
- Notion API key + Database ID ([integration guide](https://developers.notion.com/docs/create-a-notion-integration))

### Installation

```bash
# Clone repository
git clone <repo-url>
cd us_vet_scraping

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `config/config.json` to customize:
- Search terms and geography
- Scoring weights
- Filtering criteria
- Test mode settings

### Execution

```bash
# Full pipeline (all stages)
python main.py --config config/config.json

# Test mode (10 practices only)
python main.py --config config/config.json --test

# Individual stages
python main.py --stage google-maps  # Stage 1 only
python main.py --stage enrichment   # Stage 2 only
python main.py --stage scoring      # Stage 3 only
```

---

## 📊 Cost Breakdown

| Stage | Tool | Volume | Unit Cost | Total |
|-------|------|--------|-----------|-------|
| Google Maps Scraping | Apify compass actor | 150 practices | $0.006/result | **$0.90** |
| Website Scraping | Crawl4AI | 150 websites | Free (local) | **$0.00** |
| LLM Extraction | OpenAI GPT-4o-mini | 150 extractions | $0.0006/call | **$0.10** |
| Notion API | Notion | 150 records | Free tier | **$0.00** |
| **TOTAL** | | | | **$1.00** |

*With retries/buffer: $1.10-1.30*

---

## 📁 Project Structure

```
us_vet_scraping/
├── src/
│   ├── config/
│   │   └── settings.py          # Pydantic config loader
│   ├── utils/
│   │   ├── logger.py            # Dual logging (JSON + console)
│   │   ├── retry_handler.py     # Tenacity retry decorators
│   │   └── error_tracker.py     # Error aggregation
│   ├── clients/
│   │   ├── apify_client.py      # Apify API wrapper
│   │   └── notion_client.py     # Notion API wrapper
│   ├── models/
│   │   ├── practice.py          # VeterinaryPractice model
│   │   ├── apify_models.py      # Apify response schemas
│   │   ├── website_models.py    # Website extraction schemas
│   │   └── scoring_models.py    # Lead scoring schemas
│   ├── scrapers/
│   │   ├── google_maps.py       # FEAT-001 implementation
│   │   └── website_scraper.py   # FEAT-002 implementation
│   ├── enrichment/
│   │   ├── llm_extractor.py     # OpenAI structured outputs
│   │   └── orchestrator.py      # Enrichment pipeline
│   └── scoring/
│       ├── lead_scorer.py       # FEAT-003 implementation
│       ├── classifier.py        # Practice size classification
│       └── priority_tier.py     # Tier assignment
├── config/
│   ├── config.json              # Main configuration
│   └── website_extraction_prompt.txt  # LLM extraction prompt
├── data/
│   ├── logs/                    # JSON logs
│   ├── website_cache/           # Cached HTML
│   └── raw/                     # Raw scrape data (optional)
├── tests/
│   ├── test_config.py
│   ├── test_scrapers.py
│   ├── test_enrichment.py
│   └── test_scoring.py
├── docs/
│   ├── features/                # Feature PRDs
│   ├── system/                  # Technical architecture
│   └── sop/                     # Standard operating procedures
├── .env.example                 # Environment variables template
├── requirements.txt             # Python dependencies
├── main.py                      # Entry point
└── README.md                    # This file
```

---

## 🎯 Lead Scoring Algorithm

### Scoring Dimensions (0-120 points)

**1. Practice Size (0-40 pts)**
- 3-5 vets: 40 pts (Sweet Spot)
- 6-8 vets: 35 pts (Still good)
- 9-12 vets: 25 pts (Getting large)
- 2 vets: 30 pts (Small multi-vet)
- 1 vet: 10 pts (Solo, low fit)
- 13-20 vets: 15 pts (Corporate-ish)
- 20+ vets: 5 pts (Too large)

**2. Call Volume Indicators (0-30 pts)**
- 24/7 emergency services: 15 pts
- 150+ Google reviews: 10 pts
- Boarding services: 5 pts

**3. Technology Adoption (0-20 pts)**
- Online booking: 8 pts
- Patient portal: 7 pts
- Telemedicine: 5 pts
- Digital records: 3 pts

**4. Baseline Score (0-10 pts)**
- Normalized from FEAT-001 initial score (review count + rating)

**5. Decision Maker Bonus (0-20 pts)**
- Name + Email + Role: 20 pts
- Name + Email: 15 pts
- Name + Role: 10 pts
- Name only: 5 pts

### Priority Tiers

- 🔥 **Hot (80-120 pts):** Contact ASAP (top 23%)
- 🌡️ **Warm (50-79 pts):** Contact within week (37%)
- ❄️ **Cold (20-49 pts):** Low priority (27%)
- ⛔ **Out of Scope (0-19 pts):** Skip (13%)

---

## 🗂️ Notion Database Schema

**48-field schema** organized into 7 categories:

1. **Core Data** (12 fields): Practice Name, Address, Phone, Website, Google Place ID, Rating, Reviews, etc.
2. **Enrichment Data** (8 fields): Vet count, services, technology features, operating hours
3. **Decision Maker** (6 fields): Name, role, email, LinkedIn, contact quality
4. **Personalization** (3 fields): Unique facts, awards, context for cold calling
5. **Scoring** (4 fields): Lead score, priority tier, practice size, score breakdown
6. **Sales Workflow** (8 fields): Status, assigned to, notes, next action, follow-up dates
7. **Metadata** (7 fields): Scrape dates, run ID, data sources, completeness

**De-duplication:** Primary key = Google Place ID (unique 27-char identifier)

**Update Logic:** Enrichment updates existing records, preserves sales workflow fields

See [docs/system/database.md](docs/system/database.md) for complete schema.

---

## 🔍 Website Extraction

**LLM Extraction Prompt:** `config/website_extraction_prompt.txt`

**Extracts:**
- Vet count (total + confidence level)
- Veterinarian names and specialties
- Decision maker (owner, practice manager) + contact info
- Services (emergency, specialty, boarding, etc.)
- Technology features (booking, portal, chat, etc.)
- **Personalization context** (unique facts for cold calling)

**Example Personalization Context:**
- "Recently opened 2nd location in Newton (2024)"
- "Fear-free certified practice"
- "Dr. Sarah Johnson featured in Boston Magazine Best Vets 2024"
- "Only practice in Boston specializing in exotic birds"

---

## ⚠️ Error Handling

**Retry Logic (Tenacity):**
- Apify/OpenAI: 2 retries, 5s wait
- Notion: 3 retries, exponential backoff (1s, 2s, 4s)
- Website scraping: 2 retries, 5s/10s wait

**Error Categories:**
- `apify_scraping`: Actor failures
- `website_timeout`: Scraping timeouts
- `llm_extraction`: OpenAI failures
- `notion_push`: Notion API errors
- `validation`: Data validation failures

**Error Summary:** Displayed at pipeline end with counts per category

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/ -v

# Run integration tests (requires API keys)
pytest tests/integration/ -v

# Test mode (10 practices, faster, cheaper)
python main.py --test
```

---

## 📚 Documentation

- **[System Architecture](docs/system/architecture.md)** - Pipeline design
- **[Database Schema](docs/system/database.md)** - Notion 48-field schema
- **[API Integrations](docs/system/integrations.md)** - Apify, OpenAI, Notion, Crawl4AI
- **[Technology Stack](docs/system/stack.md)** - Dependencies and versions
- **[Configuration](docs/system/configuration.md)** - Pydantic models

**Feature PRDs:**
- [FEAT-000: Shared Infrastructure](docs/features/FEAT-000_shared-infrastructure/prd.md)
- [FEAT-001: Google Maps Scraping](docs/features/FEAT-001_google-maps-notion/prd.md)
- [FEAT-002: Website Enrichment](docs/features/FEAT-002_website-enrichment/prd.md)
- [FEAT-003: Lead Scoring](docs/features/FEAT-003_lead-scoring/prd.md)

---

## 🔮 Phase 2 Roadmap

**Not in MVP:**
- LinkedIn enrichment (deferred due to cost/complexity)
- Email verification (SMTP check)
- Multi-geography support
- Recurring scraper (weekly updates)
- CRM integration (HubSpot, Salesforce)
- PMS vendor detection

---

## 🤝 Contributing

This project uses the AI Workflow Starter framework:
- `/explore [topic]` - Start feature exploration
- `/plan [FEAT-ID]` - Create planning docs
- `/build [FEAT-ID]` - Implement feature
- `/test [FEAT-ID]` - Run tests
- `/commit [message]` - Git workflow

See [CLAUDE.md](CLAUDE.md) for AI workflow details.

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙋 Support

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation:** [docs/README.md](docs/README.md)
- **PRD:** [master_PRD.md](master_PRD.md)

---

**Built with:** Python 3.11 • Apify • Crawl4AI • OpenAI GPT-4o-mini • Notion API
