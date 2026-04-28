from dotenv import load_dotenv
load_dotenv()

import json
import logging
import os
from datetime import datetime, timedelta, timezone

import resend
from groq import Groq
from supabase import create_client

from agents.fetcher import _fetch_rss, _fetch_github, _fetch_changelog

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

supabase_client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))


def get_already_alerted(user_email: str, days: int = 7) -> list[str]:
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        response = (
            supabase_client.table("breaking_change_alerts")
            .select("url")
            .eq("user_email", user_email)
            .gte("alerted_at", cutoff)
            .execute()
        )
        return [row["url"] for row in response.data if row.get("url")]
    except Exception as e:
        logger.error("Failed to query breaking_change_alerts: %s", e)
        return []


def store_alert(user_email: str, source: str, title: str, url: str) -> bool:
    try:
        supabase_client.table("breaking_change_alerts").insert({
            "user_email": user_email,
            "source": source,
            "title": title,
            "url": url,
            "alerted_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return True
    except Exception as e:
        logger.error("Failed to store breaking change alert: %s", e)
        return False


def summarize_breaking_change(title: str, content: str, source: str) -> str:
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a technical writer. Given a software release or changelog entry that contains a breaking change, write exactly 1-2 sentences explaining: what broke, and what the developer needs to do. Be specific and actionable. No markdown, no bullet points, no links. Plain text only."},
                {"role": "user", "content": f"Source: {source}\nTitle: {title}\nContent: {content[:2000]}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Failed to summarize breaking change: %s", e)
        import re
        return re.sub(r'[#*`\[\]_]', '', content[:200]).strip()


def send_breaking_change_email(alerts: list[dict], recipient_email: str) -> bool:
    try:
        resend.api_key = os.environ.get("RESEND_API_KEY", "")
        count = len(alerts)
        plural = "s" if count > 1 else ""
        sections_html = ""
        for alert in alerts:
            sections_html += f"""
  <div style="margin-bottom:32px;">
    <h2 style="font-size:17px;font-weight:700;color:#dc2626;margin:0 0 6px 0;">⚠️ {alert['source_name']}</h2>
    <p style="margin:0 0 6px 0;"><a href="{alert['url']}" style="color:#6366f1;font-weight:600;font-size:15px;">{alert['title']}</a></p>
    <p style="margin:0;color:#333;font-size:14px;line-height:1.6;">{alert['summary']}</p>
  </div>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:0 0 24px 0;">"""
        html = f"""<html>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;padding:20px;color:#333;line-height:1.6;">
  <h1 style="font-size:22px;font-weight:700;color:#1a1a2e;margin-bottom:4px;">DevStackPulse — Breaking Change{plural} Detected</h1>
  <p style="color:#6b7280;font-size:13px;margin:0 0 20px 0;">{count} breaking change{plural} found across your monitored sources.</p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:0 0 24px 0;">
  {sections_html}
  <p style="font-size:12px;color:#9ca3af;text-align:center;margin-top:16px;">Sent by <strong>DevStackPulse</strong> · Your dev stack, monitored.</p>
</body>
</html>"""
        resend.Emails.send({
            "from": "StackPulse <onboarding@resend.dev>",
            "to": [recipient_email],
            "subject": f"⚠️ DevStackPulse — {count} Breaking Change{plural} Detected",
            "html": html,
        })
        logger.info("Consolidated breaking change alert sent to %s (%d alerts)", recipient_email, count)
        return True
    except Exception as e:
        logger.error("Failed to send breaking change email: %s", e)
        return False


def run_breaking_change_check(sources: list[dict], user_email: str) -> int:
    already_alerted = get_already_alerted(user_email)
    alerted_urls = set(already_alerted)
    alerts_to_send = []

    for source in sources:
        source_name = source["name"]
        try:
            updates = []
            if source.get("rss_url"):
                try:
                    updates = _fetch_rss(source)
                except Exception:
                    pass
            if not updates and source.get("github_repo"):
                try:
                    updates = _fetch_github(source)
                except Exception:
                    pass
            if not updates and source.get("changelog_url"):
                try:
                    updates = _fetch_changelog(source)
                except Exception:
                    pass

            for update in updates:
                url = update.get("url", "")
                if url in alerted_urls:
                    continue

                try:
                    response = groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "You are a developer tool analyst. Given an update, determine if it is a breaking change that requires immediate developer attention. Return only JSON: {\"is_breaking\": bool, \"severity_reason\": str}"},
                            {"role": "user", "content": f"Source: {source_name}\nTitle: {update.get('title', '')}\nContent: {update.get('content', '')[:1000]}"}
                        ],
                        response_format={"type": "json_object"}
                    )
                    parsed = json.loads(response.choices[0].message.content)
                except Exception as e:
                    logger.warning("LLM classification failed for %s: %s", update.get("title", ""), e)
                    continue

                if not parsed.get("is_breaking"):
                    continue

                summary = summarize_breaking_change(update.get("title", ""), update.get("content", ""), source["name"])
                store_alert(user_email, source["name"], update.get("title", ""), url)
                alerted_urls.add(url)
                alerts_to_send.append({
                    "source_name": source["name"],
                    "title": update.get("title", ""),
                    "summary": summary,
                    "url": url,
                    "severity": update.get("severity", "breaking"),
                })
                logger.info("Breaking change queued: %s — %s", source["name"], update.get("title", ""))

        except Exception as e:
            logger.error("Breaking change check failed for %s: %s", source.get("name", "?"), e)

    if alerts_to_send:
        send_breaking_change_email(alerts_to_send, user_email)

    return len(alerts_to_send)
