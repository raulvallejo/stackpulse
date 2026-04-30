from dotenv import load_dotenv
load_dotenv()

import logging
import os

from supabase import create_client as create_supabase_client

from agents.orchestrator import pipeline

logging.basicConfig(level=logging.INFO, format="%(message)s")


def build_graph():
    return pipeline


def get_active_users():
    try:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        client = create_supabase_client(url, key)
        response = client.table("users").select("id, email, interests, plan").execute()
        return response.data or []
    except Exception as e:
        logging.error(f"Failed to fetch users: {e}")
        return []


def get_user_sources(user_id: str):
    try:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        client = create_supabase_client(url, key)
        response = client.table("sources").select("*").eq("user_id", user_id).execute()
        return response.data or []
    except Exception as e:
        logging.error(f"Failed to fetch sources for user {user_id}: {e}")
        return []


def convert_user_source(source_row: dict) -> dict:
    website = source_row.get("website", "") or ""
    if website and not website.startswith("http://") and not website.startswith("https://"):
        website = "https://" + website
    return {
        "name": source_row.get("name", ""),
        "website": website,
        "rss_url": None,
        "github_repo": None,
        "changelog_url": website,
        "why_interested": source_row.get("why_interested", ""),
    }


def main():
    users = get_active_users()
    if not users:
        print("No active users found.")
        return

    for user in users:
        user_email = user.get("email", "")
        user_interests = user.get("interests", "") or ""
        user_id = user.get("id", "")
        plan = user.get("plan", "free")

        print(f"Running pipeline for {user_email} (plan: {plan})...")

        user_source_rows = get_user_sources(user_id)

        if not user_source_rows:
            print(f"No sources configured for {user_email} — skipping.")
            continue

        user_sources = [convert_user_source(s) for s in user_source_rows]

        try:
            app = build_graph()
            result = app.invoke({
                "sources": user_sources,
                "user_interests": user_interests,
                "recipient_email": user_email,
                "plan": plan,
                "source_results": [],
                "digest": "",
                "quality_score": 0.0,
                "quality_breakdown": {},
                "should_send": False,
            })
            print(f"Pipeline complete for {user_email}. Quality: {result.get('quality_score', 0):.2f}")
        except Exception as e:
            logging.error(f"Pipeline failed for {user_email}: {e}")
            continue


if __name__ == "__main__":
    main()
