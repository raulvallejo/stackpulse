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
        for source_result in updates:
            source_name = source_result.get("source", "")
            for update in source_result.get("filtered_updates", []):
                if update.get("severity") == "breaking":
                    continue
                rows.append({
                    "user_email": user_email,
                    "source": source_name,
                    "title": update.get("title", ""),
                    "url": update.get("url", ""),
                    "severity": update.get("severity", "informational"),
                    "sent_at": datetime.now(timezone.utc).isoformat()
                })
        if not rows:
            logger.info("No non-breaking updates to store")
            return True
        supabase_client.table("sent_updates").insert(rows).execute()
        logger.info(f"Stored {len(rows)} updates to memory for {user_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to store updates to memory: {e}")
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
    if not previously_sent_urls:
        return source_results
    filtered_count = 0
    for source_result in source_results:
        original = source_result.get("filtered_updates", [])
        kept = []
        for update in original:
            if update.get("severity") == "breaking":
                kept.append(update)
            elif update.get("url") and update.get("url") not in previously_sent_urls:
                kept.append(update)
            elif not update.get("url"):
                kept.append(update)
            else:
                filtered_count += 1
        source_result["filtered_updates"] = kept
    logger.info(f"Memory filter removed {filtered_count} already-seen updates")
    return source_results
