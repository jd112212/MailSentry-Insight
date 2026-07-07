import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List
import pandas as pd

from modules.gmail_connector import GmailConnector
from modules.email_fetcher import EmailFetcher
from modules.text_cleaner import TextCleaner
from modules.classifier import EmailClassifier
from modules.parser import EmailParser
from modules.csv_exporter import CSVExporter
from modules.analytics_dashboard import AnalyticsDashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MailSentry Insight™ API",
    description="Enterprise Email Intelligence & Analytics Engine Backend Service",
    version="2.0"
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, we permit all origins. Change to specific ports in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = "config.json"
OUTPUT_DIR = "output"

class ConfigSchema(BaseModel):
    username: str
    app_password: str
    fetch_limit: int = 50
    append_mode: bool = True

def load_config() -> Dict[str, Any]:
    """Reads configuration from config.json if present."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading configuration file: {e}")
            return {}
    return {}

def save_config_file(config_data: Dict[str, Any]):
    """Writes configuration settings to config.json."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=4)

@app.get("/api/config/status")
def get_config_status():
    """Returns whether Gmail configuration is initialized, along with basic settings."""
    config = load_config()
    is_configured = bool(config.get("username") and config.get("app_password"))
    return {
        "configured": is_configured,
        "username": config.get("username", ""),
        "fetch_limit": config.get("fetch_limit", 50),
        "append_mode": config.get("append_mode", True)
    }

@app.post("/api/config")
def save_config(config: ConfigSchema):
    """Saves Gmail settings to configuration file."""
    try:
        config_data = config.dict()
        save_config_file(config_data)
        logger.info("Saved configuration successfully.")
        return {"status": "success", "message": "Configuration updated successfully."}
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")

@app.post("/api/fetch")
def trigger_fetch():
    """
    Core pipeline execution endpoint. Connects to Gmail, fetches emails,
    cleans, classifies, extracts entities, updates CSV files, and regenerates charts.
    """
    config = load_config()
    username = config.get("username")
    app_password = config.get("app_password")
    limit = config.get("fetch_limit", 50)
    append_mode = config.get("append_mode", True)

    if not username or not app_password:
        raise HTTPException(
            status_code=400,
            detail="Gmail account credentials are not configured. Please complete settings first."
        )

    connector = GmailConnector(username, app_password)
    try:
        # Step 1: Gmail Connection
        mail_conn = connector.connect()

        # Step 2: Fetch raw emails
        fetcher = EmailFetcher(mail_conn)
        raw_emails = fetcher.fetch_recent_emails(limit=limit)

        # Disconnect safely
        connector.disconnect()

        if not raw_emails:
            return {
                "status": "success",
                "message": "Inbox synchronization complete. No recent emails found.",
                "fetched_count": 0
            }

        # Step 3: Run pipeline
        cleaner = TextCleaner(remove_stopwords=True)
        classifier = EmailClassifier()
        parser = EmailParser()

        processed_emails = []
        extracted_entities = []

        for email_item in raw_emails:
            # Preprocess body text for classification
            clean_body = cleaner.clean_text(email_item["body"])

            # Classification
            category = classifier.classify(email_item["subject"], clean_body)

            # Clean and truncate preview body for CSV integrity (removes tags, breaks)
            preview = email_item["body"][:150]
            preview = cleaner.strip_html(preview).replace("\n", " ").replace("\r", " ").strip()
            if len(email_item["body"]) > 150:
                preview += "..."

            processed_emails.append({
                "email_id": email_item["email_id"],
                "sender": email_item["sender"],
                "subject": email_item["subject"],
                "date": email_item["date"],
                "category": category,
                "body_preview": preview
            })

            # Extract structured entity data (run on original body to preserve details)
            entities = parser.extract_entities(
                email_item["email_id"],
                email_item["subject"],
                email_item["body"]
            )
            extracted_entities.append(entities)

        # Step 4: Export to CSV files
        exporter = CSVExporter(output_dir=OUTPUT_DIR, append_mode=append_mode)
        exporter.export_data(processed_emails, extracted_entities)

        # Step 5: Regenerate Matplotlib Analytics & summaries
        dashboard = AnalyticsDashboard(output_dir=OUTPUT_DIR)
        metrics = dashboard.generate_metrics_and_charts()

        return {
            "status": "success",
            "message": f"Successfully synchronized and analyzed {len(processed_emails)} emails.",
            "fetched_count": len(processed_emails),
            "metrics": metrics
        }

    except ValueError as ve:
        # Invalid credentials/authentication
        raise HTTPException(status_code=401, detail=f"Authentication Failure: {str(ve)}")
    except Exception as e:
        logger.exception("Error executing email intelligence pipeline:")
        raise HTTPException(status_code=500, detail=f"Inbox sync error: {str(e)}")

@app.get("/api/emails")
def get_emails():
    """Retrieves processed email records from local CSV file."""
    path = os.path.join(OUTPUT_DIR, "processed_emails.csv")
    if not os.path.exists(path):
        return []
    try:
        df = pd.read_csv(path)
        df = df.fillna("N/A")
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error reading emails CSV: {e}")
        raise HTTPException(status_code=500, detail="Failed to load processed emails data.")

@app.get("/api/entities")
def get_entities():
    """Retrieves extracted entities records from local CSV file."""
    path = os.path.join(OUTPUT_DIR, "extracted_entities.csv")
    if not os.path.exists(path):
        return []
    try:
        df = pd.read_csv(path)
        df = df.fillna("N/A")
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error reading entities CSV: {e}")
        raise HTTPException(status_code=500, detail="Failed to load extracted entities data.")

@app.get("/api/analytics")
def get_analytics():
    """Generates charts and aggregates metrics on the fly, returning statistics json."""
    dashboard = AnalyticsDashboard(output_dir=OUTPUT_DIR)
    metrics = dashboard.generate_metrics_and_charts()
    return metrics

@app.get("/api/charts/{chart_name}")
def get_chart_image(chart_name: str):
    """Serves the generated PNG charts directly as file response."""
    # Sanitize inputs to prevent directory traversal
    clean_name = chart_name.replace("..", "").replace("/", "").replace("\\", "")
    chart_path = os.path.join(OUTPUT_DIR, f"{clean_name}.png")
    if not os.path.exists(chart_path):
        raise HTTPException(status_code=404, detail="Requested analytics chart does not exist.")
    return FileResponse(chart_path, media_type="image/png")

# Serve the static frontend files
# Mounted at root "/" to serve index.html automatically. Must be registered last.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
