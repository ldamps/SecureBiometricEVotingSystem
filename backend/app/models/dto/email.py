"""DTOs for email sending."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SendEmailDTO:
    """Data needed to send a single email."""

    to_email: str
    subject: str
    template_name: str
    template_vars: Dict[str, str] = field(default_factory=dict)
