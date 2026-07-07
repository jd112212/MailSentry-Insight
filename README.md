# MailSentry-Insight

Enterprise Email Intelligence & Analytics Engine — Flask backend + browser dashboard frontend.

## ⚠️ Security first
`config.json` in this package already contains the Gmail address and App Password
you shared in chat, so you can run it immediately. **Please rotate that App Password**
in your Google Account (Security → App Passwords) once you're done testing, since it
was shared in plain text in a chat conversation. Going forward, never paste real
passwords into chat — edit `config.json` directly on your machine instead.

`config.json` is already excluded via `.gitignore` — never commit it to GitHub.

## Setup

```bash
cd MailSentry_Insight
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Your MailSentry Insight™ FastAPI backend is now live:

🌐 App URL	**http://localhost:8000**
📡 API Docs	**http://localhost:8000/docs**
🔄 Status	Running with --reload (auto-restarts on file changes)

Server startup log confirmed:
INFO: Uvicorn running on **http://0.0.0.0:8000** (Press CTRL+C to quit)
INFO: Application startup complete.

To use the app:
1.Open your browser → go to **http://localhost:8000**
2.Go to Connection Settings tab → enter your Gmail address + Google App Password
3.Click Save Configuration
4.Click Sync Inbox on the dashboard to fetch & analyze your emails

## Project structure
```
MailSentry_Insight/
├── main.py                     # Flask backend + API routes
├── config.json                 # Gmail credentials (excluded from git)
├── requirements.txt
├── modules/
│   ├── gmail_connector.py      # FR1 - IMAP auth
│   ├── email_fetcher.py        # FR2 - retrieval
│   ├── text_cleaner.py         # FR3 - preprocessing
│   ├── classifier.py           # FR4 - classification
│   ├── parser.py               # FR5 - regex entity extraction
│   ├── csv_exporter.py         # FR6 - CSV export
│   └── analytics_dashboard.py  # FR7 - charts + summary
├── frontend/
│   └── index.html              # Dashboard UI
└── output/                     # Generated CSVs + PNGs (created at runtime)
```

## API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/run` | POST | Runs the full pipeline end-to-end |
| `/api/emails` | GET | Returns processed_emails.csv as JSON |
| `/api/entities` | GET | Returns extracted_entities.csv as JSON |
| `/output/<file>` | GET | Serves generated CSV/PNG files |

## Notes
- No external AI APIs are used — classification is pure keyword-weighted scoring (FR4),
  and entity extraction is pure regex (FR5), per SRS scope.
- The pipeline skips unreadable emails/failed regex matches instead of crashing (NFR2).
- CSV export de-duplicates by `email_id` and supports append mode (FR6, config.json → `csv.append_mode`).
