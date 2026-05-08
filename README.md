# Atlas Memory MCP Server

High Token-optimized Memory-enhanced MCP Server for **OpenCode**, **Cline**, and **Claude Code**.

Provides code knowledge graph, session memory, and semantic search with minimal token overhead.

## Features

- **5 MCP Tools** — 4 direct tools + 1 `exec_code` sandbox tool
- **Code Knowledge Graph** — tree-sitter powered Python AST parsing (functions, classes, calls, imports)
- **Semantic Search** — ChromaDB + OpenAI text-embedding-3-small
- **Memory Lifecycle** — automatic cleanup of stale data with configurable TTL
- **JS Sandbox** — `exec_code` tool runs custom JavaScript against in-memory entity graph
- **Auto-Index** — automatically indexes your project on startup

## Requirements

- Python >= 3.10
- Node.js >= 18 (for `exec_code` tool only)
- OpenAI API Key (for semantic search)

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Run

```bash
# Set required env var
export OPENAI_API_KEY="sk-..."

# Start MCP server (stdio mode)
python -m atlas_memory.server
```

### 3. Configure Client

**OpenCode** (`opencode.jsonc`):
```jsonc
{
  "mcpServers": {
    "atlas-memory": {
      "command": "python",
      "args": ["-m", "atlas_memory.server"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "PROJECT_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

**Cline** (`mcp_settings.json`):
```json
{
  "mcpServers": {
    "atlas-memory": {
      "command": "python",
      "args": ["-m", "atlas_memory.server"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "PROJECT_ROOT": "/absolute/path"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `search_entities` | Search code entities by keyword/semantic/hybrid |
| `get_relations` | Query call/import/extend relationships |
| `list_observations` | List observation notes for an entity |
| `add_observation` | Add an observation note |
| `exec_code` | Execute custom JS against memory graph |

### exec_code Examples

```javascript
// Find all auth-related functions
const results = mem.query('auth', {type: 'function', limit: 10});
return results.map(r => ({name: r.name, file: r.path}));

// Get who calls a function
const rels = mem.relations('abc123::login', 'in');
return rels.map(r => r.from_name);

// Check observations on an entity
const notes = mem.observations('abc123::login');
return notes.map(n => n.content);
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `PROJECT_ROOT` | `./` | Project directory to index |
| `MEMORY_DB_PATH` | `./data/memory.db` | SQLite database path |
| `CHROMA_PATH` | `./data/chroma` | ChromaDB persistence path |
| `AUTO_INDEX` | `true` | Auto-index on startup |
| `MAX_INDEX_FILE_SIZE_KB` | `200` | Skip files larger than this |
| `SERVER_PORT` | `8742` | SSE/HTTP port |
| `FORGETTING_MAX_AGE_DAYS` | `90` | Max observation age |
| `FORGETTING_MAX_INACTIVE_DAYS` | `30` | Entity inactivity threshold |
| `FORGETTING_BUDGET_KEEP_TOP_N` | `10000` | Max entity count |
| `FORGETTING_EVERY_MINUTES` | `60` | Cleanup interval |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev,ai]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/atlas_memory --cov-report=term-missing
```

## Architecture

```
atlas-memory-mcp/
├── src/atlas_memory/
│   ├── server.py          # FastMCP entry + 5 tools
│   ├── config.py          # Environment config
│   ├── models/            # Entity/Relation/Observation
│   ├── storage/           # SQLite database layer
│   ├── tools/             # Tool implementations
│   ├── memory/            # Graph engine + Vector search + Lifecycle
│   ├── parser/            # tree-sitter code parser
│   └── sandbox/           # JS executor + API bridge
└── tests/
```
