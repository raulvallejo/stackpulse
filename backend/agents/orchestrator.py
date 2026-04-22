from dotenv import load_dotenv
load_dotenv()

import json
import os
from typing import TypedDict

import opik
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

from agents.fetcher import fetch_all_sources
from mailer.sender import send_digest
from sources.sources import get_sources


def _safe_track(*args, **kwargs):
    try:
        return opik.track(*args, **kwargs)
    except Exception:
        def noop(fn): return fn
        return noop


opik_client = opik.Opik()
filter_prompt = opik_client.get_prompt(name="stackpulse-filter", project_name="stackpulse")
synthesize_prompt = opik_client.get_prompt(name="stackpulse-synthesize", project_name="stackpulse")
score_prompt = opik_client.get_prompt(name="stackpulse-score", project_name="stackpulse")

llm = ChatGroq(model="llama-3.3-70b-versatile")


class StackPulseState(TypedDict):
    sources: list[dict]
    raw_updates: dict[str, list[dict]]
    filtered_updates: dict[str, list[dict]]
    digest: str
    quality_score: float
    quality_breakdown: dict
    should_send: bool
    recipient_email: str
    user_interests: str


@_safe_track
def load_sources(state: StackPulseState) -> StackPulseState:
    state["sources"] = get_sources()
    state["recipient_email"] = os.environ.get("RECIPIENT_EMAIL", "")
    state["user_interests"] = os.environ.get("USER_INTERESTS", "")
    return state


@_safe_track
def fetch_all(state: StackPulseState) -> StackPulseState:
    state["raw_updates"] = fetch_all_sources()
    return state


@_safe_track
def filter_updates(state: StackPulseState) -> StackPulseState:
    filtered = {}
    for source in state["sources"]:
        name = source["name"]
        updates = state["raw_updates"].get(name, [])
        prompt_text = filter_prompt.format(
            source_name=name,
            why_interested=source.get("why_interested", ""),
            updates=json.dumps(updates),
            user_interests=state["user_interests"],
        )
        try:
            response = llm.invoke(prompt_text)
            parsed = json.loads(response.content)
            if parsed:
                filtered[name] = parsed
        except Exception:
            pass
    state["filtered_updates"] = filtered
    return state


@_safe_track
def synthesize(state: StackPulseState) -> StackPulseState:
    prompt_text = synthesize_prompt.format(
        user_interests=state["user_interests"],
        filtered_updates=json.dumps(state["filtered_updates"]),
    )
    response = llm.invoke(prompt_text)
    state["digest"] = response.content
    return state


@_safe_track
def score_digest(state: StackPulseState) -> StackPulseState:
    prompt_text = score_prompt.format(
        user_interests=state["user_interests"],
        digest=state["digest"],
    )
    response = llm.invoke(prompt_text)
    parsed = json.loads(response.content)
    state["quality_score"] = parsed.get("score", 0.0)
    state["quality_breakdown"] = parsed.get("breakdown", {})
    state["should_send"] = state["quality_score"] >= 0.6
    return state


@_safe_track
def send_email(state: StackPulseState) -> StackPulseState:
    if not state["should_send"]:
        print(f"Digest score {state['quality_score']:.2f} below threshold — email not sent.")
        return state
    send_digest(digest=state["digest"], recipient=state["recipient_email"])
    return state


_graph = StateGraph(StackPulseState)
_graph.add_node("load_sources", load_sources)
_graph.add_node("fetch_all", fetch_all)
_graph.add_node("filter_updates", filter_updates)
_graph.add_node("synthesize", synthesize)
_graph.add_node("score_digest", score_digest)
_graph.add_node("send_email", send_email)

_graph.add_edge(START, "load_sources")
_graph.add_edge("load_sources", "fetch_all")
_graph.add_edge("fetch_all", "filter_updates")
_graph.add_edge("filter_updates", "synthesize")
_graph.add_edge("synthesize", "score_digest")
_graph.add_edge("score_digest", "send_email")
_graph.add_edge("send_email", END)

pipeline = _graph.compile()


@_safe_track(name="stackpulse-pipeline")
def run_pipeline():
    result = pipeline.invoke({})
    score = result.get("quality_score", 0.0)
    sent = result.get("should_send", False)
    print(f"Quality score: {score:.2f}")
    print(f"Email sent: {sent}")
