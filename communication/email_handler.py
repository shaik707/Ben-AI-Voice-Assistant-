# communication/email_handler.py — Email System
# SMTP for sending, IMAP for reading

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
import os
import json
import datetime


class EmailHandler:
    """
    Full email system with SMTP send and IMAP read.
    Supports: send, read inbox, read unread, search, mark read, attachments.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.email_address = self.config.get("email", "")
        self.email_password = self.config.get("password", "")
        self.smtp_server = self.config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.imap_server = self.config.get("imap_server", "imap.gmail.com")
        self.imap_port = self.config.get("imap_port", 993)

    def is_configured(self):
        """Check if email credentials are configured."""
        return bool(self.email_address and self.email_password)

    # ==================== SEND EMAIL ====================

    def send_email(self, to_address, subject, body, attachments=None):
        """
        Send an email via SMTP.
        attachments: list of file paths to attach.
        """
        if not self.is_configured():
            return "Email not configured. Please set email credentials in settings."

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_address
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'rb') as f:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{os.path.basename(filepath)}"'
                            )
                            msg.attach(part)
                        except Exception as e:
                            print(f"[Email] Attachment error for {filepath}: {e}")

            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)

            return f"Email sent to {to_address} with subject '{subject}'."

        except smtplib.SMTPAuthenticationError:
            return "Email authentication failed. Check your email and app password."
        except Exception as e:
            return f"Email send error: {str(e)}"

    # ==================== READ EMAILS ====================

    def read_inbox(self, count=10, unread_only=False):
        """
        Read emails from inbox.
        Returns list of email summaries.
        """
        if not self.is_configured():
            return "Email not configured."

        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select('inbox')

            criteria = 'UNSEEN' if unread_only else 'ALL'
            status, messages = mail.search(None, criteria)

            if status != 'OK':
                mail.logout()
                return "Could not search inbox."

            email_ids = messages[0].split()
            if not email_ids:
                mail.logout()
                return "No emails found." if not unread_only else "No unread emails."

            # Get latest emails
            latest_ids = email_ids[-count:]
            results = []

            for eid in reversed(latest_ids):
                try:
                    status, data = mail.fetch(eid, '(RFC822)')
                    if status != 'OK':
                        continue
                    msg = email.message_from_bytes(data[0][1])

                    subject = self._decode_header(msg['Subject'])
                    sender = self._decode_header(msg['From'])
                    date = msg['Date']

                    # Get body preview
                    body_preview = self._get_body(msg)[:200]

                    results.append({
                        "id": eid.decode(),
                        "from": sender,
                        "subject": subject,
                        "date": date,
                        "preview": body_preview,
                        "read": criteria != 'UNSEEN'
                    })
                except Exception as e:
                    print(f"[Email] Parse error: {e}")
                    continue

            mail.logout()

            if not results:
                return "No emails to display."

            # Format output
            lines = [f"{'Unread' if unread_only else 'Inbox'} ({len(results)} emails):"]
            for i, em in enumerate(results, 1):
                lines.append(f"\n  {i}. From: {em['from']}")
                lines.append(f"     Subject: {em['subject']}")
                lines.append(f"     Date: {em['date']}")
                lines.append(f"     Preview: {em['preview']}...")

            return "\n".join(lines)

        except imaplib.IMAP4.error as e:
            return f"IMAP error: {str(e)}"
        except Exception as e:
            return f"Email read error: {str(e)}"

    def read_unread(self, count=10):
        """Read unread emails."""
        return self.read_inbox(count=count, unread_only=True)

    def search_emails(self, query, field="subject", count=10):
        """
        Search emails by subject, sender, or body.
        field: 'subject', 'from', 'body', 'all'
        """
        if not self.is_configured():
            return "Email not configured."

        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select('inbox')

            # Build IMAP search criteria
            if field == "subject":
                criteria = f'(SUBJECT "{query}")'
            elif field == "from":
                criteria = f'(FROM "{query}")'
            elif field == "body":
                criteria = f'(BODY "{query}")'
            else:
                criteria = f'(OR (SUBJECT "{query}") (FROM "{query}"))'

            status, messages = mail.search(None, criteria)
            email_ids = messages[0].split() if status == 'OK' else []

            if not email_ids:
                mail.logout()
                return f"No emails found matching '{query}'."

            results = []
            for eid in reversed(email_ids[-count:]):
                try:
                    status, data = mail.fetch(eid, '(RFC822)')
                    if status != 'OK':
                        continue
                    msg = email.message_from_bytes(data[0][1])
                    subject = self._decode_header(msg['Subject'])
                    sender = self._decode_header(msg['From'])
                    results.append({"from": sender, "subject": subject, "date": msg['Date']})
                except Exception:
                    continue

            mail.logout()

            lines = [f"Search results for '{query}' ({len(results)} found):"]
            for i, em in enumerate(results, 1):
                lines.append(f"  {i}. {em['from']} — {em['subject']} ({em['date']})")
            return "\n".join(lines)

        except Exception as e:
            return f"Search error: {str(e)}"

    def mark_as_read(self, email_id):
        """Mark an email as read by ID."""
        if not self.is_configured():
            return "Email not configured."
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select('inbox')
            mail.store(email_id.encode(), '+FLAGS', '\\Seen')
            mail.logout()
            return f"Email {email_id} marked as read."
        except Exception as e:
            return f"Error: {str(e)}"

    # ==================== Helpers ====================

    def _decode_header(self, header):
        """Decode email header."""
        if not header:
            return "(No subject)"
        decoded_parts = decode_header(header)
        parts = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                parts.append(part.decode(charset or 'utf-8', errors='replace'))
            else:
                parts.append(str(part))
        return ' '.join(parts)

    def _get_body(self, msg):
        """Extract plain text body from email message."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        return part.get_payload(decode=True).decode(errors='replace')
                    except Exception:
                        pass
        else:
            try:
                return msg.get_payload(decode=True).decode(errors='replace')
            except Exception:
                pass
        return "(No text content)"
