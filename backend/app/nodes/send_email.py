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
  to      (str): fallback recipient — used only when the incoming payload
                 does not contain an "email" key (optional if payload provides it)
  subject (str): email subject (default: "Workflow Notification")

Recipient resolution order:
  1. payload["email"]  — set by an upstream node (e.g. Manual Trigger)
  2. config["to"]      — static fallback configured on the node
  If neither is present, execution raises NodeExecutionError.

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

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Payload email takes priority over the static config fallback
        to: str = str(payload.get("email") or self.config.get("to") or "")
        if not to:
            raise NodeExecutionError(
                "SendEmailNode: no recipient found. "
                "Add an 'email' key to the trigger payload or set a fallback "
                "address in the node's 'To' field."
            )

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
