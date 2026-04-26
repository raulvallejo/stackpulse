import logging
import os
import re

import markdown
import resend

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

_SUBJECT = "StackPulse — Your Weekly Dev Stack Digest"


def send_digest(digest: str, recipient: str) -> bool:
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

        html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6;">
{html_body}
<hr style="border:none;border-top:1px solid #e5e7eb;margin:30px 0 10px;">
<p style="font-size:12px;color:#9ca3af;text-align:center;margin:0;">Sent by <strong>StackPulse</strong> · Your dev stack, monitored.</p>
</body>
</html>
"""
        resend.Emails.send({
            "from": "StackPulse <onboarding@resend.dev>",
            "to": [recipient],
            "subject": _SUBJECT,
            "html": html,
        })
        logger.info("Digest sent to %s", recipient)
        return True
    except Exception as exc:
        logger.error("Failed to send digest: %s", exc)
        return False
