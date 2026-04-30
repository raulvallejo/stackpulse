import logging
import os
import re

import markdown
import resend

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

_SUBJECT = "DevStackPulse — Your Weekly Dev Stack Digest"


def send_digest(digest: str, recipient: str, plan: str = "free") -> bool:
    try:
        resend.api_key = os.environ.get("RESEND_API_KEY", "")

        # Strip Title: prefix if present
        lines = digest.split('\n')
        if lines[0].startswith('Title: '):
            lines[0] = lines[0].replace('Title: ', '', 1)
        digest = '\n'.join(lines)

        # Convert sources list to inline paragraph
        digest = re.sub(
            r'Sources monitored this week:\*?\*?\s*\n+((?:- .+\n?)+)',
            lambda m: 'Sources monitored this week: ' + ' · '.join(
                item.lstrip('- ').strip()
                for item in m.group(1).strip().split('\n') if item.strip()
            ) + '\n',
            digest
        )

        # Convert markdown to HTML
        html_body = markdown.markdown(digest, extensions=['extra', 'nl2br'])

        # Style the title
        html_body = re.sub(
            r'<p>(Your Weekly Dev Stack Digest[^<]+)</p>',
            r'<h1 style="font-size:28px;font-weight:700;color:#1a1a2e;margin-bottom:4px;margin-top:0;">\1</h1>',
            html_body,
            count=1
        )

        # Add horizontal rules between h2 sections
        html_body = html_body.replace('<h2>', '<hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;"><h2 style="color:#1a1a2e;font-size:16px;font-weight:700;margin-bottom:8px;">')

        upgrade_section = ""
        if plan == "free":
            upgrade_section = """
<div style="border:2px solid #0d9488;border-radius:8px;padding:16px 20px;margin:24px 0;background:#f0fdfa;">
  <p style="margin:0;font-size:14px;color:#0f766e;">🚀 <strong>Upgrade to Pro</strong> — Monitor up to 15 sources and receive instant breaking change alerts.</p>
  <p style="margin:8px 0 0 0;font-size:13px;"><a href="https://www.devstackpulse.com/pricing" style="color:#0d9488;font-weight:600;">Upgrade now →</a></p>
</div>"""

        html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6;">
{html_body}
{upgrade_section}
<hr style="border:none;border-top:1px solid #e5e7eb;margin:30px 0 10px;">
<p style="font-size:12px;color:#9ca3af;text-align:center;margin:0 0 6px 0;">Sent by <strong>DevStackPulse</strong> · Your dev stack, monitored.</p>
<p style="font-size:12px;color:#9ca3af;text-align:center;margin:0;"><a href="https://www.devstackpulse.com" style="color:#9ca3af;">Visit DevStackPulse to manage your sources and interests.</a></p>
</body>
</html>
"""
        resend.Emails.send({
            "from": "DevStackPulse <digest@devstackpulse.com>",
            "to": [recipient],
            "subject": _SUBJECT,
            "html": html,
        })
        logger.info("Digest sent to %s", recipient)
        return True
    except Exception as exc:
        logger.error("Failed to send digest: %s", exc)
        return False
