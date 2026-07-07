import os
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CSVExporter:
    """
    Exports processed email and entity records to CSV files.
    Ensures data fields are correctly formatted, and duplicate entries (by email_id) are avoided.
    """
    def __init__(self, output_dir: str = "output", append_mode: bool = True):
        self.output_dir = output_dir
        self.append_mode = append_mode

        # Ensure directory is created
        os.makedirs(self.output_dir, exist_ok=True)

        self.emails_path = os.path.join(self.output_dir, "processed_emails.csv")
        self.entities_path = os.path.join(self.output_dir, "extracted_entities.csv")

    def export_data(self, processed_emails: List[Dict[str, Any]], extracted_entities: List[Dict[str, Any]]):
        """
        Takes processed email dictionaries and entity dictionaries, and writes them to files.
        Avoids duplicates based on 'email_id'.
        """
        # Create DataFrames
        email_cols = ["email_id", "sender", "subject", "date", "category", "body_preview"]
        entity_cols = ["email_id", "phone_number", "invoice_id", "ticket_id", "amount", "order_id"]

        df_emails_new = pd.DataFrame(processed_emails)
        df_entities_new = pd.DataFrame(extracted_entities)

        # Standardize structure if empty
        if df_emails_new.empty:
            df_emails_new = pd.DataFrame(columns=email_cols)
        else:
            df_emails_new = df_emails_new.reindex(columns=email_cols).fillna("N/A")

        if df_entities_new.empty:
            df_entities_new = pd.DataFrame(columns=entity_cols)
        else:
            df_entities_new = df_entities_new.reindex(columns=entity_cols).fillna("N/A")

        # 1. Process emails file
        if self.append_mode and os.path.exists(self.emails_path):
            try:
                df_old = pd.read_csv(self.emails_path)
                df_combined = pd.concat([df_old, df_emails_new], ignore_index=True)
                # Keep last record if duplicates exist
                df_combined = df_combined.drop_duplicates(subset=["email_id"], keep="last")
                df_combined.to_csv(self.emails_path, index=False)
                logger.info(f"Emails CSV updated (append). Total rows: {len(df_combined)}")
            except Exception as e:
                logger.error(f"Error appending to emails CSV: {e}. Rewriting file.")
                df_emails_new.to_csv(self.emails_path, index=False)
        else:
            df_emails_new.to_csv(self.emails_path, index=False)
            logger.info(f"Emails CSV written (overwrite/new). Rows: {len(df_emails_new)}")

        # 2. Process entities file
        if self.append_mode and os.path.exists(self.entities_path):
            try:
                df_old = pd.read_csv(self.entities_path)
                df_combined = pd.concat([df_old, df_entities_new], ignore_index=True)
                # Keep last record if duplicates exist
                df_combined = df_combined.drop_duplicates(subset=["email_id"], keep="last")
                df_combined.to_csv(self.entities_path, index=False)
                logger.info(f"Entities CSV updated (append). Total rows: {len(df_combined)}")
            except Exception as e:
                logger.error(f"Error appending to entities CSV: {e}. Rewriting file.")
                df_entities_new.to_csv(self.entities_path, index=False)
        else:
            df_entities_new.to_csv(self.entities_path, index=False)
            logger.info(f"Entities CSV written (overwrite/new). Rows: {len(df_entities_new)}")
