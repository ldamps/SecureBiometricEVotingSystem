"""Email client using Resend API + Jinja2 templates."""

from pathlib import Path
from typing import Dict

import resend
import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import EMAIL_FROM, RESEND_API_KEY
from app.infra.email.exceptions import EmailSendError

logger = structlog.get_logger()

TEMPLATES_DIR = Path(__file__).parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


class ResendEmailClient:
    """Sends transactional emails via the Resend API."""

    def __init__(self) -> None:
        resend.api_key = RESEND_API_KEY

    def send(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_vars: Dict[str, str] | None = None,
    ) -> None:
        """Render an HTML template and send it via Resend."""
        template = _jinja_env.get_template(template_name)
        html_body = template.render(**(template_vars or {}))

        logger.info(
            "Sending email",
            to=to_email,
            subject=subject,
            template=template_name,
        )

        try:
            resend.Emails.send({
                "from": EMAIL_FROM,
                "to": to_email,
                "subject": subject,
                "html": html_body,
            })
        except Exception as exc:
            logger.error("Resend send failed", to=to_email, error=str(exc))
            raise EmailSendError(f"Failed to send email to {to_email}") from exc

        logger.info("Email sent successfully", to=to_email)
