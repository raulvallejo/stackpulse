# StackPulse — Agent Guide

## Project Overview

StackPulse monitors 8 developer tools and APIs for meaningful changes (breaking changes, new endpoints, deprecations, important updates) and delivers a personalized weekly email digest every Monday at 8am.

Sources monitored: Anthropic, Groq, OPIK, LangChain, LangGraph, Pinecone, Tavily, MCP Protocol.

Pipeline: fetch updates from RSS feeds, GitHub Releases API, and changelog pages → filter what matters using an LLM → synthesize a digest → score with LLM-as-judge → deliver via email.

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM | Claude Haiku 4.5 `claude-haiku-4-5-20251001` (filter + synthesize + score) |
| Embeddings | OpenAI `text-embedding-3-small` (v2) |
| Vector store | Pinecone (v2) |
| Database + auth | Supabase |
| Email delivery | Resend |
| Observability | OPIK by Comet |
| API | FastAPI |
| Scheduler | Render Cron Job |
| Deployment | Render Starter |

---

## Architecture

LangGraph graph — node execution order:

```
load_sources → fetch_all (parallel) → filter → synthesize → score → send_email
```

- **load_sources** — reads source definitions from config/DB into graph state
- **fetch_all** — fans out to all sources in parallel, each via `fetch_source()`
- **filter** — LLM pass to keep only meaningful changes per source
- **synthesize** — LLM pass to write the unified weekly digest
- **score** — LLM-as-judge scores digest quality before sending
- **send_email** — delivers final digest via Resend

Graph state must be typed with `TypedDict`.

---

## Sources

| Source | Fetch method | Details |
|---|---|---|
| Anthropic | Changelog page scraping | — |
| Groq | GitHub Releases API | `groq/groq-python` |
| OPIK | GitHub Releases API | `comet-ml/opik` |
| LangChain | RSS feed | — |
| LangGraph | GitHub Releases API | `langchain-ai/langgraph` |
| Pinecone | Changelog page scraping | — |
| Tavily | GitHub Releases API | `tavily-ai/tavily-python` |
| MCP Protocol | GitHub Releases API | `modelcontextprotocol/python-sdk` |

### Fetching hierarchy (per source)

1. RSS feed — if available
2. GitHub Releases API — if a repo is configured
3. Changelog page scraping — fallback

---

## Data-Driven Architecture

Sources are defined as a list of dicts. There are **never** hardcoded per-source fetch functions. One generic `fetch_source()` handles all sources based on the dict fields (`rss_url`, `github_repo`, `changelog_url`).

Example source dict shape:

```python
{
    "name": "LangGraph",
    "rss_url": None,
    "github_repo": "langchain-ai/langgraph",
    "changelog_url": None,
    "why_interested": "Core orchestration framework for this project",
}
```

---

## Supabase Schema

```sql
users (
    id          uuid primary key,
    email       text,
    created_at  timestamptz
)

sources (
    id             uuid primary key,
    user_id        uuid references users(id),
    name           text,
    changelog_url  text,
    github_repo    text,
    rss_url        text,
    why_interested text,
    created_at     timestamptz
)

digests (
    id             uuid primary key,
    content        text,
    sent_at        timestamptz,
    quality_score  numeric
)
```

---

## Environment Variables

```
GROQ_API_KEY
OPENAI_API_KEY
OPIK_API_KEY
OPIK_PROJECT_NAME=stackpulse
OPIK_WORKSPACE=ra-l-vallejo
PINECONE_API_KEY
PINECONE_INDEX_NAME=stackpulse
SUPABASE_URL
SUPABASE_KEY
RESEND_API_KEY
GITHUB_TOKEN
RECIPIENT_EMAIL
```

Never commit API keys. Use `.env` locally and Render environment variables in production.

---

## OPIK Instrumentation

- Configure via environment variables only — **never call `opik.configure()`**
- Use the `_safe_track` decorator pattern to wrap traced functions so that OPIK failures never crash the pipeline

---

## Versioning Plan

| Version | Scope |
|---|---|
| v1 | Personal use, 1 user, hardcoded config |
| v1.1 | Mem0 memory layer |
| v1.2 | Human-in-the-loop review for breaking changes |
| v2 | Multi-user, Supabase auth, sign-up form |

---

## Critical Rules

- Never commit API keys
- Sources must always be data-driven (list of dicts) — never hardcoded per-source logic
- LangGraph graph state must be typed with `TypedDict`

---

## Known Gotchas

### OPIK
- Never call `opik.configure()` — configure via env vars only (`OPIK_API_KEY`, `OPIK_PROJECT_NAME`, `OPIK_WORKSPACE`)
- Use the `_safe_track` decorator pattern to avoid crashes if OPIK is unavailable
- Get prompts from Prompt Library using `opik.Opik().get_prompt(name="...")` — never hardcode prompts in Python

### Pinecone
- `$contains` metadata filter not supported on free tier — use standard similarity search only
- Connect to existing index, never create it in code

### LangChain
- Use `langchain_text_splitters` not `langchain.text_splitter`

### LangGraph
- Always define state with `TypedDict` — never use plain dict

### Groq
- Model name is `"llama-3.3-70b-versatile"` not `"llama-3.3-70b"`
- `llama-3.1-8b-instant` filters too aggressively — returned empty results for all sources. Switched all nodes to Claude Haiku for consistent quality. Score improved from 0.62 to 0.87.

### GitHub API
- Always load `GITHUB_TOKEN` from env — unauthenticated requests limited to 60/hour

### Render
- Use `@app.api_route("/", methods=["GET","HEAD"])` for health check endpoints to handle both GET and HEAD requests
- Free tier spins down after inactivity — use Starter plan for portfolio services

### MCP SSE Transport
- Use `mcp.sse_app()` with Starlette wrapper for remote MCP servers
- `mcp-remote` config needs `timeout: 30000` to handle cold start delays

### Environment Variables
- Always use `os.environ.get()` not `os.environ[]` to prevent crashes on missing vars
