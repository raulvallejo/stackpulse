from dotenv import load_dotenv
load_dotenv()

import os

from agents.breaking_change_agent import run_breaking_change_check
from sources.sources import get_sources


def main():
    sources = get_sources()
    user_email = os.environ.get("RECIPIENT_EMAIL", "")
    print(f"Running daily breaking change check for {user_email}")
    print(f"Checking {len(sources)} sources...")
    count = run_breaking_change_check(sources, user_email)
    print(f"Daily check complete. {count} new breaking change alerts sent.")


if __name__ == "__main__":
    main()
