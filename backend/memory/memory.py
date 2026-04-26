from dotenv import load_dotenv
load_dotenv()

import logging
import os
from datetime import datetime, timedelta, timezone

from supabase import create_client

logger = logging.getLogger(__name__)

supabase_client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)


def store_sent_updates(updates: list[dict], user_email: str) -> bool:
    try:
        rows = []
        for update in updates:
            if update.get("severity") == "breaking":
                continue
            rows.append({
                "user_email": user_email,
                "source": update.get("source", ""),
                "title": update.get("title", ""),
                "url": update.get("url", ""),
                "severity": update.get("severity", ""),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            })
        if rows:
            supabase_client.table("sent_updates").insert(rows).execute()
        logger.info("Stored %d updates to memory for %s", len(rows), user_email)
        return True
    except Exception as e:
        logger.error("Failed to store updates to memory: %s", e)
        return False


def get_previously_sent(user_email: str, days: int = 7) -> list[str]:
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        response = (
            supabase_client.table("sent_updates")
            .select("url")
            .eq("user_email", user_email)
            .gte("sent_at", cutoff)
            .execute()
        )
        urls = [row["url"] for row in response.data if row.get("url")]
        logger.info("Found %d previously sent updates in memory", len(urls))
        return urls
    except Exception as e:
        logger.error("Failed to retrieve previously sent updates: %s", e)
        return []


def filter_already_sent(source_results: list[dict], previously_sent_urls: list[str]) -> list[dict]:
    sent_set = set(previously_sent_urls)
    filtered_results = []
    total_removed = 0

    for result in source_results:
        original = result.get("filtered_updates", [])
        kept = [
            u for u in original
            if u.get("url") not in sent_set or u.get("severity") == "breaking"
        ]
        total_removed += len(original) - len(kept)
        filtered_results.append({**result, "filtered_updates": kept})

    logger.info("Memory filter removed %d already-seen updates", total_removed)
    return filtered_results
