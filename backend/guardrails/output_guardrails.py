from dotenv import load_dotenv
load_dotenv()

import logging
import re

logger = logging.getLogger(__name__)


def validate_digest(digest: str, quality_score: float, source_results: list[dict]) -> dict:
    reasons_blocked = []
    warnings = []

    # Check 1 — Technical failure only
    if digest is None or len(digest.strip()) == 0:
        reasons_blocked.append("Digest is empty — technical failure in synthesis")

    # Check 2 — Quality threshold
    if quality_score < 0.6:
        reasons_blocked.append(f"Quality score {quality_score:.2f} below threshold 0.6")

    # Check 3 — No updates warning
    if all(not r.get("filtered_updates") for r in source_results):
        warnings.append("No sources had updates this week — digest may be generic")

    # Check 4 — Hallucination check
    known_sources = {r["source"].lower() for r in source_results if r.get("source")}
    if digest:
        headers = re.findall(r'^##\s+(.+)$', digest, re.MULTILINE)
        for header in headers:
            header_clean = header.strip().lower()
            if not any(known in header_clean or header_clean in known for known in known_sources):
                warnings.append(f"Unrecognized source in digest: {header.strip()}")

    return {
        "should_send": len(reasons_blocked) == 0,
        "reasons_blocked": reasons_blocked,
        "warnings": warnings,
    }


def log_guardrail_result(result: dict) -> None:
    if result["reasons_blocked"]:
        logger.warning("GUARDRAIL BLOCKED: %s", "; ".join(result["reasons_blocked"]))
    if result["warnings"]:
        logger.warning("GUARDRAIL WARNING: %s", "; ".join(result["warnings"]))
    if not result["reasons_blocked"] and not result["warnings"]:
        logger.info("GUARDRAIL PASSED: digest approved for sending")
