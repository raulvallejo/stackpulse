# StackPulse

**Your dev stack, monitored. Weekly digest, delivered.**

StackPulse is an AI agent that monitors the APIs and developer tools you build on, detects breaking changes, new endpoints, and deprecations, and delivers a personalized weekly email digest. Built with LangGraph, Anthropic Claude, and OPIK.

---

## How It Works

Every Monday at 8am, an Orchestrator Agent uses LangGraph's Send API to dispatch one Source Agent per tool in parallel. Each Source Agent fetches updates (RSS / GitHub Releases / changelog scraping) and filters them with Claude Haiku. Results are accumulated and passed to a Synthesis Agent that writes the digest, a Quality Agent that scores it with LLM-as-judge, and a Delivery Agent that sends it via Resend.

```
Orchestrator
  └─ load_config → dispatch (Send API, parallel)
       ├─ Source Agent × 8  (fetch → filter)
            ↓
       synthesize → score → send_email
```

### Sources Monitored

- Anthropic
- Groq
- OPIK
- LangChain
- LangGraph
- Pinecone
- Tavily
- MCP Protocol

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM | Claude Haiku 4.5 (filter + synthesis + scoring) |
| Email delivery | Resend |
| Database + auth | Supabase |
| Observability | OPIK |
| API | FastAPI |
| Deployment | Render |

---

## Roadmap

| Version | Scope |
|---------|-------|
| v1 | Personal use, 1 user, hardcoded config. LangGraph pipeline, OPIK tracing, prompts in Prompt Library, Resend email, Render Cron Job |
| v1.1 | Observability depth — cost tracking, latency per node, quality scores over time, alerts |
| v1.2 | Evals — LLM-as-judge rubrics in OPIK, baseline scores, regression detection |
| v1.3 | Guardrails — input/output validation, hallucination checks, OWASP LLM Top 10 mapped |
| v1.4 | Memory with Mem0 — never repeat same update, personalization improves over time |
| v1.5 | Human-in-the-loop — breaking changes trigger immediate alert, LangGraph interrupt pattern |
| v2 | Multi-user — Supabase auth, sign-up form, per-user source configuration, per-user digest personalization |
| v3 | Full product — dashboard, digest history, source management UI |

---

## Setup

### Environment Variables

Create a `.env` file in the `backend/` directory with:

```
ANTHROPIC_API_KEY=
GROQ_API_KEY=
OPIK_API_KEY=
OPIK_PROJECT_NAME=stackpulse
OPIK_WORKSPACE=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=stackpulse
SUPABASE_URL=
SUPABASE_KEY=
RESEND_API_KEY=
GITHUB_TOKEN=
RECIPIENT_EMAIL=
USER_INTERESTS=
```

---

## Author

Built by [Raul Vallejo](https://linkedin.com/in/raulvallejo) — PM building and shipping production AI agents.

---

MIT License
