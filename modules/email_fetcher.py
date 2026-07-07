import email
from email.header import decode_header
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EmailFetcher:
    """
    Fetches the last N emails and parses their metadata and text body.
    """
    def __init__(self, mail_connection):
        self.mail = mail_connection

    def fetch_recent_emails(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetches the last N emails from the INBOX.
        Handles failures gracefully for individual emails.
        """
        emails_list = []
        try:
            logger.info("Selecting Gmail 'INBOX' folder...")
            status, messages = self.mail.select("INBOX", readonly=True)
            if status != 'OK':
                raise ValueError("Failed to select INBOX.")

            # Retrieve all email IDs
            status, data = self.mail.search(None, "ALL")
            if status != 'OK':
                raise ValueError("Failed to search INBOX emails.")

            email_ids = data[0].split()
            total_emails = len(email_ids)
            logger.info(f"Discovered {total_emails} total emails.")

            # Filter to last N email IDs (configured limit)
            target_ids = email_ids[-limit:] if total_emails > limit else email_ids
            # Process in reverse (most recent first)
            target_ids = list(reversed(target_ids))

            for index, mail_id_bytes in enumerate(target_ids):
                mail_id = mail_id_bytes.decode('utf-8')
                try:
                    status, message_data = self.mail.fetch(mail_id_bytes, "(RFC822)")
                    if status != 'OK':
                        logger.warning(f"Could not fetch email ID {mail_id}. Skipping.")
                        continue

                    raw_email = message_data[0][1]
                    if not raw_email:
                        logger.warning(f"No content found for email ID {mail_id}. Skipping.")
                        continue

                    # Parse raw email message
                    msg = email.message_from_bytes(raw_email)

                    # Extract headers
                    subject = self._decode_header_value(msg.get("Subject", ""))
                    sender = self._decode_header_value(msg.get("From", ""))
                    date_val = msg.get("Date", "")

                    # Extract body text
                    body = self._extract_body(msg)

                    emails_list.append({
                        "email_id": mail_id,
                        "sender": sender,
                        "subject": subject,
                        "date": date_val,
                        "body": body
                    })

                except Exception as e:
                    # NFR2: Skip single email errors without crashing the entire system
                    logger.error(f"Error processing email ID {mail_id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise e

        return emails_list

    def _decode_header_value(self, header_value: str) -> str:
        """
        Decodes MIME-encoded headers (e.g. Subject, From).
        """
        if not header_value:
            return ""
        try:
            decoded_parts = decode_header(header_value)
            decoded_text = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    encoding = encoding if encoding else "utf-8"
                    try:
                        decoded_text += part.decode(encoding, errors="replace")
                    except Exception:
                        decoded_text += part.decode("utf-8", errors="replace")
                else:
                    decoded_text += str(part)
            return decoded_text
        except Exception:
            return str(header_value)

    def _extract_body(self, msg) -> str:
        """
        Extracts body plain text from email message. If plain text is not
        available, extracts HTML content as fallback.
        """
        body_parts = []
        try:
            if msg.is_multipart():
                # Walk through email parts
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    # Select plain text preferentially
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_parts.append(payload.decode(part.get_content_charset() or 'utf-8', errors='replace'))
                    # Fallback to HTML if plain text is not present
                    elif content_type == "text/html" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload and not body_parts: # only append if plain body is empty so far
                            body_parts.append(payload.decode(part.get_content_charset() or 'utf-8', errors='replace'))
                body = "\n".join(body_parts)
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(msg.get_content_charset() or 'utf-8', errors='replace')
                else:
                    body = ""
        except Exception as e:
            logger.warning(f"Error parsing email body payload: {e}")
            body = ""
        return body
