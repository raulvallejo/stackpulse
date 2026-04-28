from dotenv import load_dotenv
load_dotenv()

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import time
import threading

import feedparser
import opik
import requests
from bs4 import BeautifulSoup
from groq import Groq
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

_LOOKBACK_DAYS = 7
_CHANGELOG_MAX_CHARS = 3000


def _safe_track(*args, **kwargs):
    try:
        return opik.track(*args, **kwargs)
    except Exception:
        def noop(fn): return fn
        return noop


USE_GROQ_FILTER = os.environ.get("USE_GROQ_FILTER", "true").lower() == "true"

opik_client = opik.Opik()
filter_prompt = opik_client.get_prompt(name="stackpulse-filter", project_name="stackpulse")

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

_anthropic_semaphore = threading.Semaphore(5)
_groq_lock = threading.Lock()
_groq_last_call_time = 0.0


class SourceAgentState(TypedDict):
    source: dict
    user_interests: str
    raw_updates: list[dict]
    filtered_updates: list[dict]
    error: str | None


def _cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)


def _parse_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        import time
        ts = time.mktime(value)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        return None


def _fetch_rss(source: dict) -> list[dict]:
    feed = feedparser.parse(source["rss_url"])
    cutoff = _cutoff()
    results = []
    for entry in feed.entries:
        published_dt = _parse_dt(getattr(entry, "published_parsed", None))
        if published_dt and published_dt < cutoff:
            continue
        results.append({
            "source": source["name"],
            "title": getattr(entry, "title", ""),
            "content": getattr(entry, "summary", ""),
            "url": getattr(entry, "link", ""),
            "published": published_dt.isoformat() if published_dt else None,
        })
    return results


def _fetch_github(source: dict) -> list[dict]:
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{source['github_repo']}/releases"
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    cutoff = _cutoff()
    results = []
    for release in response.json():
        published_str = release.get("published_at") or release.get("created_at")
        published_dt = None
        if published_str:
            published_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        if published_dt and published_dt < cutoff:
            continue
        results.append({
            "source": source["name"],
            "title": release.get("name") or release.get("tag_name", ""),
            "content": release.get("body", ""),
            "url": release.get("html_url", ""),
            "published": published_dt.isoformat() if published_dt else None,
        })
    return results


def _fetch_changelog(source: dict) -> list[dict]:
    response = requests.get(source["changelog_url"], timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    main = soup.find("main") or soup.find("article") or soup.body
    text = main.get_text(separator="\n", strip=True) if main else ""
    truncated = text[:_CHANGELOG_MAX_CHARS]

    return [{
        "source": source["name"],
        "title": f"{source['name']} Changelog",
        "content": truncated,
        "url": source["changelog_url"],
        "published": None,
    }]


@_safe_track
def fetch_source_node(state: SourceAgentState) -> SourceAgentState:
    source = state["source"]
    state["error"] = state.get("error")

    try:
        if source.get("rss_url"):
            try:
                state["raw_updates"] = _fetch_rss(source)
                logger.info("Fetched %s via RSS", source["name"])
                return state
            except Exception as exc:
                logger.warning("RSS fetch failed for %s: %s", source["name"], exc)

        if source.get("github_repo"):
            try:
                state["raw_updates"] = _fetch_github(source)
                logger.info("Fetched %s via GitHub Releases", source["name"])
                return state
            except Exception as exc:
                logger.warning("GitHub fetch failed for %s: %s", source["name"], exc)

        if source.get("changelog_url"):
            try:
                state["raw_updates"] = _fetch_changelog(source)
                logger.info("Fetched %s via changelog page", source["name"])
                return state
            except Exception as exc:
                logger.warning("Changelog fetch failed for %s: %s", source["name"], exc)

        state["raw_updates"] = []
    except Exception as exc:
        logger.error("fetch_source_node failed for %s: %s", source.get("name", "?"), exc)
        state["error"] = str(exc)
        state["raw_updates"] = []

    return state


@_safe_track
def filter_source_node(state: SourceAgentState) -> SourceAgentState:
    try:
        source = state["source"]
        updates_str = json.dumps(state.get("raw_updates", []))
        if len(updates_str) > 8000:
            updates_str = updates_str[:8000]

        prompt_text = filter_prompt.format(
            source_name=source["name"],
            why_interested=source.get("why_interested", ""),
            updates=updates_str,
            user_interests=state["user_interests"],
        )

        if USE_GROQ_FILTER:
            model_name = "llama-3.3-70b-versatile"
            global _groq_last_call_time
            with _groq_lock:
                elapsed = time.time() - _groq_last_call_time
                if elapsed < 13.0:
                    time.sleep(13.0 - elapsed)
                groq_response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt_text}],
                )
                _groq_last_call_time = time.time()
            raw = groq_response.choices[0].message.content or ""
match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                raw = match.group(0)
            else:
                raw = "[]"
        else:
            model_name = "claude-haiku-4-5-20251001"
            with _anthropic_semaphore:
                response = llm.invoke(prompt_text)
            raw = response.content
            if isinstance(raw, list):
                raw = raw[0].text if hasattr(raw[0], "text") else str(raw[0])

        try:
            opik.opik_context.update_current_span(metadata={"model": model_name})
        except Exception:
            pass

        if not USE_GROQ_FILTER:
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
        state["filtered_updates"] = json.loads(raw)
    except Exception as exc:
        logger.warning("filter_source_node failed for %s: %s", state["source"].get("name", "?"), exc)
        state["filtered_updates"] = []

    return state


_graph = StateGraph(SourceAgentState)
_graph.add_node("fetch_source_node", fetch_source_node)
_graph.add_node("filter_source_node", filter_source_node)
_graph.add_edge(START, "fetch_source_node")
_graph.add_edge("fetch_source_node", "filter_source_node")
_graph.add_edge("filter_source_node", END)

source_agent = _graph.compile()
