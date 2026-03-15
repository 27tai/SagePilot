"""
Send Email node.

Sends the entire incoming payload as a formatted JSON email body to a
configured recipient address.

SMTP credentials are read from environment variables — never stored in
node config:
  SMTP_HOST      (default: localhost)
  SMTP_PORT      (default: 587)
  SMTP_USER      (default: "")
  SMTP_PASSWORD  (default: "")
  SMTP_FROM      (default: SMTP_USER)
  SMTP_USE_TLS   (default: "true")  — set to "false" to disable STARTTLS
  SMTP_MOCK      (default: "false") — set to "true" to skip sending and
                                      log the email to stdout instead

Config keys (stored in workflow):
  to      (str): recipient email address (required)
  subject (str): email subject (default: "Workflow Notification")

Output: incoming payload passed through unchanged, with an added key:
  email_sent (bool): True on success
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from .base import BaseNode, NodeExecutionError

logger = logging.getLogger(__name__)


class SendEmailNode(BaseNode):
    node_type = "send_email"

    def validate_config(self) -> None:
        if not self.config.get("to"):
            raise ValueError("SendEmailNode: 'to' (recipient address) is required.")

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_config()

        to: str = self.config["to"]
        subject: str = self.config.get("subject") or "Workflow Notification"

        mock: bool = os.getenv("SMTP_MOCK", "false").lower() == "true"
        smtp_host: str = os.getenv("SMTP_HOST", "localhost")
        smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        smtp_user: str = os.getenv("SMTP_USER", "")
        smtp_password: str = os.getenv("SMTP_PASSWORD", "")
        smtp_from: str = os.getenv("SMTP_FROM", smtp_user)
        use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() != "false"

        body_text = json.dumps(payload, indent=2, default=str)

        if mock:
            logger.info(
                "SendEmailNode [MOCK] to=%s subject=%r\n%s",
                to, subject, body_text,
            )
            return {**payload, "email_sent": True, "email_mock": True}

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to

        msg.attach(MIMEText(body_text, "plain"))

        html = (
            "<html><body>"
            f"<p>Workflow payload:</p>"
            f"<pre style='font-family:monospace;background:#f4f4f4;padding:12px;"
            f"border-radius:4px;font-size:13px;'>{body_text}</pre>"
            "</body></html>"
        )
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls()
                if smtp_user:
                    server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from, to, msg.as_string())
        except smtplib.SMTPException as exc:
            raise NodeExecutionError(f"SendEmailNode: failed to send email — {exc}")
        except OSError as exc:
            raise NodeExecutionError(
                f"SendEmailNode: could not connect to SMTP server "
                f"{smtp_host}:{smtp_port} — {exc}"
            )

        return {**payload, "email_sent": True}
