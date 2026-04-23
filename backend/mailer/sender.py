import logging
import os

import markdown
import resend

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

_SUBJECT = "StackPulse — Your Weekly Dev Stack Digest"


def send_digest(digest: str, recipient: str) -> bool:
    try:
        resend.api_key = os.environ.get("RESEND_API_KEY", "")
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333;">
{markdown.markdown(digest, extensions=['extra'])}
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
