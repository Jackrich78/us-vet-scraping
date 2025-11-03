# Notes - Archon Integration

## Archon MCP - Core Capabilities Confirmed

**Key Features:**

- **Knowledge Base:** Web crawling, document uploads (PDF/docs), RAG search
- **Task Management:** Project creation, task tracking integrated with knowledge
- **Real-time Updates:** Socket.IO for live collaboration
- **MCP Server:** Connects to Claude Code, Cursor, Windsurf, etc.
- **Agents Service:** PydanticAI-based agents for document/RAG operations

**Architecture:**

- Microservices: UI (port 3737), Server (8181), MCP (8051), Agents (8052)
- Stack: FastAPI, React/TypeScript, Supabase (PostgreSQL + PGVector)
- Docker-based deployment

## Integration Points with Your Workflow

### Archon's Role:

1. **Central Memory:** Store scraped documentation, framework references, library docs
2. **Project Planning:** Track tasks, features, PRDs, technical specs
3. **Context Provider:** Feed relevant docs to AI assistants via MCP
4. **Agent Orchestration:** PydanticAI agents already built in

### Questions Emerging:

1. **Local Setup:** You mentioned needing to move it locally - is this about running your own instance vs. hosted?
2. **Sub-Agent Integration:** Archon has PydanticAI agents built-in - should these be your sub-agents, or separate?
3. **Slash Command Integration:** How do slash commands interact with Archon's MCP tools?
4. **Knowledge Sync:** When you crawl docs, how does this feed into your project templates?

## Revised Workflow Understanding

`[Archon Knowledge Base] ← Crawled Docs + PDFs
         ↓
[Project in Archon] ← Tasks, PRDs, Features
         ↓
[MCP Connection] → Claude/AI Assistant
         ↓
[Sub-Agents] ← Access Archon knowledge
         ↓
[Development Flow] → Updates back to Archon tasks`