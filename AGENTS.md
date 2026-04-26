# StackPulse — Agent Guide

## Project Overview

StackPulse monitors 8 developer tools and APIs for meaningful changes (breaking changes, new endpoints, deprecations, important updates) and delivers a personalized weekly email digest every Monday at 8am.

Sources monitored: Anthropic, Groq, OPIK, LangChain, LangGraph, Pinecone, Tavily, MCP Protocol.

Pipeline: fetch updates from RSS feeds, GitHub Releases API, and changelog pages → filter what matters using an LLM → synthesize a digest → score with LLM-as-judge → deliver via email.

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph + LangGraph Send API for parallel agent dispatch |
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

Multi-agent system built with LangGraph. The orchestrator uses the Send API to dispatch one Source Agent per source in parallel, then passes aggregated results through synthesis, scoring, and delivery.

```
Orchestrator
  └─ load_config → dispatch_sources (Send API)
       ├─ Source Agent [Anthropic]  (fetch → filter)
       ├─ Source Agent [Groq]       (fetch → filter)
       ├─ Source Agent [OPIK]       (fetch → filter)
       ├─ Source Agent [LangChain]  (fetch → filter)
       ├─ Source Agent [LangGraph]  (fetch → filter)
       ├─ Source Agent [Pinecone]   (fetch → filter)
       ├─ Source Agent [Tavily]     (fetch → filter)
       └─ Source Agent [MCP]        (fetch → filter)
            ↓ (all results accumulated via operator.add)
       synthesize → score → send_email
```

### Agents

- **Orchestrator** (`agents/orchestrator.py`) — supervisor graph. Loads config, uses `Send` API to fan out to parallel Source Agents, then runs synthesis → scoring → delivery.
- **Source Agent** (`agents/fetcher.py`) — one instance per source, runs in parallel. Two-node LangGraph: `fetch_source_node` → `filter_source_node`. Fetches via RSS / GitHub Releases / changelog scraping, then filters with Claude Haiku.
- **Synthesis Agent** (node inside orchestrator) — combines all source results into a unified digest with Claude Haiku.
- **Quality Agent** (node inside orchestrator) — LLM-as-judge scores the digest before sending. Threshold: 0.6.
- **Delivery Agent** (node inside orchestrator) — sends final digest via Resend if quality threshold is met.
- **Breaking Change Agent** *(coming next iteration)* — separate daily cron job for immediate alerts on breaking changes.

All graph states typed with `TypedDict`.

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
ANTHROPIC_API_KEY
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
| v1 ✅ | Core pipeline, OPIK tracing, Resend email, Render Cron Job |
| v1.1 ✅ | Observability depth: quality score as OPIK feedback score, quality breakdown metadata, token usage + cost tracking, sources stats |
| v1.3 ✅ | Guardrails: input validation (source reachability), output validation (empty digest, quality threshold, hallucination check) |
| v1.4 ✅ | Memory: Supabase sent_updates table, deduplication of non-breaking updates, breaking changes always resurface |
| v1.5 ✅ | Breaking Change Agent: daily cron (0 9 * * *), Groq classification + summarization, keyword pre-filter, Supabase breaking_change_alerts table, immediate email alerts |
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
- `opik_client.update_trace()` requires `project_name` parameter: `opik_client.update_trace(trace_id=trace_id, project_name="stackpulse", metadata={...})`
- `opik_client.log_traces_feedback_scores()` takes a list of score dicts: `[{"id": trace_id, "name": "quality_score", "value": score, "reason": "..."}]`

### Pinecone
- `$contains` metadata filter not supported on free tier — use standard similarity search only
- Connect to existing index, never create it in code

### LangChain
- Use `langchain_text_splitters` not `langchain.text_splitter`

### LangGraph
- Always define state with `TypedDict` — never use plain dict
- **Send API dispatch**: `dispatch_sources` must be a conditional edge, not a node — wire it with `add_conditional_edges("load_config", dispatch_sources, ["run_source_agent"])`. Using `add_node` instead silently breaks fan-out.
- **Parallel result accumulation**: use `Annotated[list[dict], operator.add]` on accumulator fields (e.g. `source_results`) so each parallel agent's return is merged by concatenation, not overwritten.
- **Partial state returns from Send nodes**: `run_source_agent` returns only `{"source_results": [...]}`, not the full `OrchestratorState`. Nodes dispatched via `Send` should only write back the fields they own.

### Anthropic
- Haiku rate limits with 16+ parallel source agents — use `threading.Semaphore(5)` in `filter_source_node` to limit concurrent calls
- `sources_with_updates` count must check `len(filtered_updates) > 0`, not just truthiness

### Groq
- Model name is `"llama-3.3-70b-versatile"` not `"llama-3.3-70b"`
- `llama-3.1-8b-instant` filters too aggressively — returned empty results for all sources. Switched all nodes to Claude Haiku 4.5 for consistent quality. Score improved from 0.62 to 0.87.
- Free tier has a 100,000 tokens per day (TPD) limit. During development, running the pipeline multiple times burns through this quickly. In production (weekly runs) this is not an issue.
- All 3 nodes (filter, synthesize, score) now use Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) via Anthropic API. Groq is kept as a monitored source but no longer used as LLM provider.

### GitHub API
- Always load `GITHUB_TOKEN` from env — unauthenticated requests limited to 60/hour

### Render
- Use `@app.api_route("/", methods=["GET","HEAD"])` for health check endpoints to handle both GET and HEAD requests
- Free tier spins down after inactivity — use Starter plan for portfolio services

### MCP SSE Transport
- Use `mcp.sse_app()` with Starlette wrapper for remote MCP servers
- `mcp-remote` config needs `timeout: 30000` to handle cold start delays

### Guardrails
- Input guardrail uses HEAD requests to validate source URLs. RSS feeds may fail HEAD requests but still work for fetching — this produces false positive "unreachable" warnings. These are warnings only, not blocks — pipeline continues correctly.
- Output guardrail delegates the send decision entirely — remove the old `should_send` state check from `send_email` node or it will conflict.

### Supabase / Memory
- Supabase requires the secret key (`sb_secret_...`) for backend inserts — publishable key returns 401 on writes due to RLS
- `store_sent_updates` expects `source_results` structure: `list[{"source": str, "filtered_updates": list[dict]}]` — not flat update dicts
- Memory query runs BEFORE storing — first run always finds 0 previously sent URLs, second run finds previous updates. This is correct behavior.
- Delete empty rows after fixing schema issues: `DELETE FROM sent_updates WHERE title = '' OR title IS NULL`

### Environment Variables
- Always use `os.environ.get()` not `os.environ[]` to prevent crashes on missing vars
