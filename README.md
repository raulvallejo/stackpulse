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
|---|---|
| v1 | Personal use, 1 user |
| v1.1 | Memory layer with Mem0 |
| v1.2 | Human-in-the-loop for breaking changes |
| v2 | Multi-user, sign-up form, Supabase auth |

---

## Setup

_Coming soon._

---

## Author

Built by [Raul Vallejo](https://linkedin.com/in/raulvallejo) — PM building and shipping production AI agents.

---

MIT License
