import logging
import os
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

from sources.sources import get_sources

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

_LOOKBACK_DAYS = 7
_CHANGELOG_MAX_CHARS = 3000


def _cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)


def _parse_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    # feedparser time_struct
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


def fetch_source(source: dict) -> list[dict]:
    try:
        if source.get("rss_url"):
            results = _fetch_rss(source)
            logger.info("Fetched %s via RSS", source["name"])
            return results
    except Exception as exc:
        logger.warning("RSS fetch failed for %s: %s", source["name"], exc)

    try:
        if source.get("github_repo"):
            results = _fetch_github(source)
            logger.info("Fetched %s via GitHub Releases", source["name"])
            return results
    except Exception as exc:
        logger.warning("GitHub fetch failed for %s: %s", source["name"], exc)

    try:
        if source.get("changelog_url"):
            results = _fetch_changelog(source)
            logger.info("Fetched %s via changelog page", source["name"])
            return results
    except Exception as exc:
        logger.warning("Changelog fetch failed for %s: %s", source["name"], exc)

    return []


def fetch_all_sources() -> dict[str, list[dict]]:
    results = {}
    for source in get_sources():
        print(f"Fetching {source['name']}...")
        results[source["name"]] = fetch_source(source)
    return results
