# StackPulse

**Your dev stack, monitored. Weekly digest, delivered.**

StackPulse is an AI agent that monitors the APIs and developer tools you build on, detects breaking changes, new endpoints, and deprecations, and delivers a personalized weekly email digest. Built with LangGraph, Groq, and OPIK.

---

## How It Works

Every Monday at 8am, StackPulse fetches updates from 8 developer tools via RSS feeds, GitHub Releases API, and changelog pages. An LLM filters what actually matters, synthesizes a digest, scores it for quality, and delivers it to your inbox.

```
load_sources → fetch_all → filter → synthesize → score → send_email
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
| LLM | Groq |
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

_Coming soon._

---

## Author

Built by [Raul Vallejo](https://linkedin.com/in/raulvallejo) — PM building and shipping production AI agents.

---

MIT License
