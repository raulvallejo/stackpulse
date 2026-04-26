from dotenv import load_dotenv
load_dotenv()

import logging
import os

import requests

logger = logging.getLogger(__name__)


def validate_sources(sources: list[dict]) -> dict:
    valid = []
    invalid = []

    for source in sources:
        name = source.get("name", "unknown")
        reachable = False
        last_error = "no URL configured"

        if source.get("changelog_url"):
            try:
                r = requests.head(source["changelog_url"], timeout=5, allow_redirects=True)
                if r.status_code < 400:
                    reachable = True
            except Exception as e:
                last_error = str(e)

        if not reachable and source.get("github_repo"):
            try:
                headers = {"Accept": "application/vnd.github+json"}
                token = os.environ.get("GITHUB_TOKEN")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                r = requests.get(
                    f"https://api.github.com/repos/{source['github_repo']}",
                    headers=headers,
                    timeout=5,
                )
                if r.status_code < 400:
                    reachable = True
            except Exception as e:
                last_error = str(e)

        if not reachable and source.get("rss_url"):
            try:
                r = requests.head(source["rss_url"], timeout=5, allow_redirects=True)
                if r.status_code < 400:
                    reachable = True
            except Exception as e:
                last_error = str(e)

        if reachable:
            valid.append(source)
        else:
            logger.warning("Source %s unreachable: %s", name, last_error)
            invalid.append({"source": name, "reason": last_error})

    return {
        "valid": valid,
        "invalid": invalid,
        "total": len(sources),
        "valid_count": len(valid),
        "invalid_count": len(invalid),
    }


def check_minimum_sources(validation_result: dict, minimum: int = 3) -> bool:
    if validation_result["valid_count"] >= minimum:
        return True
    logger.warning(
        "Only %d valid source(s) — minimum required is %d",
        validation_result["valid_count"],
        minimum,
    )
    return False
