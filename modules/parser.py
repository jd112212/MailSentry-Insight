import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EmailParser:
    """
    Parses raw emails using compiled regex patterns to extract structured entity records.
    Ensures single-regex failures do not abort overall parsing.
    """
    def __init__(self):
        # 1. Phone numbers: Matches +1-234-567-8900, (123) 456 7890, +91 9876543210, etc.
        self.phone_pattern = re.compile(
            r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        )

        # 2. Email addresses: Matches standard emails
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        )

        # 3. Invoice IDs: Matches INV-XXXX (where XXXX is alphanumeric, 4 to 8 characters)
        self.invoice_pattern = re.compile(
            r'\bINV-[A-Za-z0-9]{4,8}\b', re.IGNORECASE
        )

        # 4. Ticket IDs: Matches TCK-XXXX (alphanumeric, 4 to 8 characters)
        self.ticket_pattern = re.compile(
            r'\bTCK-[A-Za-z0-9]{4,8}\b', re.IGNORECASE
        )

        # 5. Monetary values: Matches symbols like ₹, $, €, £, or Rs. followed by digits
        self.monetary_pattern = re.compile(
            r'(?:[\$\u20B9\u00A3\u20AC\u00A5]|Rs\.?)\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        )

        # 6. Order IDs: Matches ORD-XXXX or phrases like 'Order #XXXX' / 'order id: XXXX'
        self.order_pattern = re.compile(
            r'\bORD-[A-Za-z0-9]{4,8}\b|\b(?:order\s*#?\s*|order[-_]?id\s*[:#\-]?\s*)([A-Za-z0-9]{4,12})\b', re.IGNORECASE
        )

    def extract_entities(self, email_id: str, subject: str, raw_body: str) -> Dict[str, Any]:
        """
        Scans raw email text (subject + body) for entities.
        NFR2: Guarantees individual pattern errors are caught without crash.
        """
        search_text = f"{subject}\n{raw_body}"
        entities = {
            "email_id": email_id,
            "phone_number": "N/A",
            "invoice_id": "N/A",
            "ticket_id": "N/A",
            "amount": "N/A",
            "order_id": "N/A"
        }

        # Extract Phone
        try:
            match = self.phone_pattern.search(search_text)
            if match:
                entities["phone_number"] = match.group(0).strip()
        except Exception as e:
            logger.warning(f"Phone regex error: {e}")

        # Extract Invoice ID
        try:
            match = self.invoice_pattern.search(search_text)
            if match:
                entities["invoice_id"] = match.group(0).strip().upper()
        except Exception as e:
            logger.warning(f"Invoice ID regex error: {e}")

        # Extract Ticket ID
        try:
            match = self.ticket_pattern.search(search_text)
            if match:
                entities["ticket_id"] = match.group(0).strip().upper()
        except Exception as e:
            logger.warning(f"Ticket ID regex error: {e}")

        # Extract Monetary Amount
        try:
            match = self.monetary_pattern.search(search_text)
            if match:
                entities["amount"] = match.group(0).strip()
        except Exception as e:
            logger.warning(f"Amount regex error: {e}")

        # Extract Order ID
        try:
            match = self.order_pattern.search(search_text)
            if match:
                # Use captured group (Order ID letters/digits) if available, else full match
                val = match.group(1) if match.group(1) else match.group(0)
                entities["order_id"] = val.strip().upper()
        except Exception as e:
            logger.warning(f"Order ID regex error: {e}")

        return entities
