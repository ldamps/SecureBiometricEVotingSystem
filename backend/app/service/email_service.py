"""Email service — sends transactional emails via Resend."""

import structlog

from app.infra.email.client import ResendEmailClient
from app.models.dto.email import SendEmailDTO

logger = structlog.get_logger()


class EmailService:
    """Thin service layer around the Resend email client."""

    def __init__(self, client: ResendEmailClient) -> None:
        self._client = client

    def send_email(self, dto: SendEmailDTO) -> None:
        """Send a single email."""
        self._client.send(
            to_email=dto.to_email,
            subject=dto.subject,
            template_name=dto.template_name,
            template_vars=dto.template_vars,
        )

    def send_registration_confirmation(self, to_email: str) -> None:
        """Send a registration confirmation email."""
        self.send_email(
            SendEmailDTO(
                to_email=to_email,
                subject="Thank you for registering to vote",
                template_name="registeration_confirmation.html",
            )
        )

    def send_official_welcome(
        self, to_email: str, first_name: str, username: str, temporary_password: str,
    ) -> None:
        """Send a welcome email to a newly created election official with their login details."""
        self.send_email(
            SendEmailDTO(
                to_email=to_email,
                subject="Your election official account has been created",
                template_name="official_welcome.html",
                template_vars={
                    "first_name": first_name or username,
                    "username": username,
                    "temporary_password": temporary_password,
                },
            )
        )

    def send_verification_code(self, to_email: str, code: str) -> None:
        """Send a 6-digit verification code for updating registration details."""
        self.send_email(
            SendEmailDTO(
                to_email=to_email,
                subject="Your verification code",
                template_name="email_verification_code.html",
                template_vars={"code": code},
            )
        )

    def send_vote_confirmation(
        self, to_email: str, vote_name: str, vote_type: str = "election"
    ) -> None:
        """Send a vote receipt / confirmation email for an election or referendum."""
        self.send_email(
            SendEmailDTO(
                to_email=to_email,
                subject=f"Vote confirmation — {vote_name}",
                template_name="voting_confirmation.html",
                template_vars={"vote_name": vote_name, "vote_type": vote_type},
            )
        )
