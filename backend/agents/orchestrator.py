from dotenv import load_dotenv
load_dotenv()

import json
import logging
import operator
import os
from typing import Annotated, TypedDict

import opik
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agents.fetcher import SourceAgentState, source_agent
from guardrails.input_guardrails import validate_sources, check_minimum_sources
from guardrails.output_guardrails import validate_digest, log_guardrail_result
from mailer.sender import send_digest
from sources.sources import get_sources

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def _safe_track(*args, **kwargs):
    try:
        return opik.track(*args, **kwargs)
    except Exception:
        def noop(fn): return fn
        return noop


opik_client = opik.Opik()
synthesize_prompt = opik_client.get_prompt(name="stackpulse-synthesize", project_name="stackpulse")
score_prompt = opik_client.get_prompt(name="stackpulse-score", project_name="stackpulse")

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

_run_metrics = {"input_tokens": 0, "output_tokens": 0}


class OrchestratorState(TypedDict):
    sources: list[dict]
    user_interests: str
    recipient_email: str
    source_results: Annotated[list[dict], operator.add]
    digest: str
    quality_score: float
    quality_breakdown: dict
    should_send: bool


@_safe_track
def load_config(state: OrchestratorState) -> OrchestratorState:
    state["sources"] = get_sources()
    state["user_interests"] = os.environ.get("USER_INTERESTS", "")
    state["recipient_email"] = os.environ.get("RECIPIENT_EMAIL", "")
    validation = validate_sources(state["sources"])
    if not check_minimum_sources(validation, minimum=3):
        print(f"WARNING: Only {validation['valid_count']} sources reachable")
    if validation["invalid"]:
        print(f"Unreachable sources: {[s['source'] for s in validation['invalid']]}")
    return state


def dispatch_sources(state: OrchestratorState) -> list[Send]:
    return [
        Send("run_source_agent", {
            "source": s,
            "user_interests": state["user_interests"],
            "raw_updates": [],
            "filtered_updates": [],
            "error": None,
        })
        for s in state["sources"]
    ]


@_safe_track
def run_source_agent(state: SourceAgentState) -> dict:
    result = source_agent.invoke(state)
    return {
        "source_results": [{
            "source": state["source"]["name"],
            "filtered_updates": result["filtered_updates"],
        }]
    }


@_safe_track
def synthesize(state: OrchestratorState) -> OrchestratorState:
    filtered = {r["source"]: r["filtered_updates"] for r in state["source_results"]}
    all_sources_list = "\n".join([f"- {s['name']}" for s in state["sources"]])
    prompt_text = synthesize_prompt.format(
        user_interests=state["user_interests"],
        filtered_updates=json.dumps(filtered),
        all_sources=all_sources_list
    )
    response = llm.invoke(prompt_text)
    if hasattr(response, 'response_metadata'):
        usage = response.response_metadata.get('usage', {})
        _run_metrics["input_tokens"] += usage.get('input_tokens', 0)
        _run_metrics["output_tokens"] += usage.get('output_tokens', 0)
    raw = response.content
    if isinstance(raw, list):
        raw = raw[0].text if hasattr(raw[0], "text") else str(raw[0])
    state["digest"] = raw
    return state


@_safe_track
def score_digest(state: OrchestratorState) -> OrchestratorState:
    prompt_text = score_prompt.format(
        user_interests=state["user_interests"],
        digest=state["digest"],
    )
    response = llm.invoke(prompt_text)
    if hasattr(response, 'response_metadata'):
        usage = response.response_metadata.get('usage', {})
        _run_metrics["input_tokens"] += usage.get('input_tokens', 0)
        _run_metrics["output_tokens"] += usage.get('output_tokens', 0)
    raw = response.content
    if isinstance(raw, list):
        raw = raw[0].text if hasattr(raw[0], "text") else str(raw[0])
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    parsed = json.loads(raw)
    state["quality_score"] = parsed.get("score", 0.0)
    state["quality_breakdown"] = parsed.get("breakdown", {})
    state["should_send"] = state["quality_score"] >= 0.6
    return state


@_safe_track
def send_email(state: OrchestratorState) -> OrchestratorState:
    guardrail_result = validate_digest(
        digest=state.get("digest", ""),
        quality_score=state.get("quality_score", 0.0),
        source_results=state.get("source_results", [])
    )
    log_guardrail_result(guardrail_result)

    if not guardrail_result["should_send"]:
        print(f"Email blocked by guardrails: {guardrail_result['reasons_blocked']}")
        return state

    send_digest(digest=state["digest"], recipient=state["recipient_email"])
    return state


_graph = StateGraph(OrchestratorState)
_graph.add_node("load_config", load_config)
_graph.add_node("run_source_agent", run_source_agent)
_graph.add_node("synthesize", synthesize)
_graph.add_node("score_digest", score_digest)
_graph.add_node("send_email", send_email)

_graph.add_edge(START, "load_config")
_graph.add_conditional_edges("load_config", dispatch_sources, ["run_source_agent"])
_graph.add_edge("run_source_agent", "synthesize")
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

    try:
        trace_data = opik.opik_context.get_current_trace_data()
        if trace_data:
            trace_id = trace_data.id

            # Log quality score as feedback score
            breakdown = result.get("quality_breakdown", {})
            opik_client.log_traces_feedback_scores(
                scores=[
                    {
                        "id": trace_id,
                        "name": "quality_score",
                        "value": score,
                        "reason": str(breakdown.get("reason", ""))
                    },
                    {
                        "id": trace_id,
                        "name": "estimated_cost_usd",
                        "value": round((_run_metrics["input_tokens"] * 0.80 + _run_metrics["output_tokens"] * 4.00) / 1_000_000, 6),
                        "reason": f"input: {_run_metrics['input_tokens']} tokens, output: {_run_metrics['output_tokens']} tokens"
                    },
                    {
                        "id": trace_id,
                        "name": "relevance",
                        "value": float(breakdown.get("relevance", 0.0)),
                        "reason": "Relevance to user interests"
                    },
                    {
                        "id": trace_id,
                        "name": "actionability",
                        "value": float(breakdown.get("actionability", 0.0)),
                        "reason": "Actionability of digest content"
                    },
                    {
                        "id": trace_id,
                        "name": "signal_to_noise",
                        "value": float(breakdown.get("signal_to_noise", 0.0)),
                        "reason": "Signal to noise ratio"
                    },
                    {
                        "id": trace_id,
                        "name": "severity_accuracy",
                        "value": float(breakdown.get("severity_accuracy", 0.0)),
                        "reason": "Accuracy of severity classification"
                    },
                    {
                        "id": trace_id,
                        "name": "timeliness",
                        "value": float(breakdown.get("timeliness", 0.0)),
                        "reason": "Timeliness of updates"
                    }
                ]
            )

            # Log metadata
            opik_client.update_trace(
                trace_id=trace_id,
                project_name="stackpulse",
                metadata={
                    "quality_breakdown": breakdown,
                    "input_tokens": _run_metrics["input_tokens"],
                    "output_tokens": _run_metrics["output_tokens"],
                    "estimated_cost_usd": round((_run_metrics["input_tokens"] * 0.80 + _run_metrics["output_tokens"] * 4.00) / 1_000_000, 6),
                    "sources_checked": len(result.get("sources", [])),
                    "sources_with_updates": len([r for r in result.get("source_results", []) if r.get("filtered_updates") and len(r.get("filtered_updates", [])) > 0]),
                }
            )

        _run_metrics["input_tokens"] = 0
        _run_metrics["output_tokens"] = 0

    except Exception as e:
        import traceback
        print(f"Failed to log OPIK metadata: {e}")
        traceback.print_exc()
