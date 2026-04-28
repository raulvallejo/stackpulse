from dotenv import load_dotenv
load_dotenv()

import logging
import os

from supabase import create_client

from agents.breaking_change_agent import run_breaking_change_check
from sources.sources import get_sources

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Single-user fallback (no longer used): RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "")

supabase_client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", ""),  # service/secret key — not the anon key
)


def get_active_users() -> list[dict]:
    try:
        response = (
            supabase_client.table("users")
            .select("id, email, plan")
            .execute()
        )
        return [
            {"id": row["id"], "email": row["email"], "plan": row["plan"]}
            for row in response.data
        ]
    except Exception as e:
        logger.error("Failed to fetch active users from Supabase: %s", e)
        return []


def main():
    sources = get_sources()
    users = get_active_users()

    if not users:
        logger.error("No users returned — exiting.")
        return

    total_alerts = 0
    for user in users:
        if user["plan"] != "pro":
            print(f"Skipping {user['email']} — free plan")
            continue
        print(f"Running breaking change check for {user['email']}...")
        count = run_breaking_change_check(sources, user["email"])
        total_alerts += count

    print(f"Daily check complete. {total_alerts} total breaking change alerts sent across all users.")


if __name__ == "__main__":
    main()
