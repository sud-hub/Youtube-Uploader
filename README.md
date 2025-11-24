# Youtube-Uploader

Repository: https://github.com/sud-hub/Youtube-Uploader.git

Simple utilities to upload videos to YouTube and extract analytics.

## Features
- Upload videos to a YouTube channel (via OAuth2).
- Set video title, description, tags and privacy status (see upload.py).
- Retrieve channel/video analytics and save output to youtube_analytics_output.json (analytics.py).
- Uses OAuth2 token stored in token.json to avoid repeated authorization.

## Files of interest
- upload.py — upload and metadata operations
- analytics.py — fetch YouTube Analytics / Reporting data
- requirements.txt — Python dependencies
- client.json — OAuth2 client credentials (not included by default)
- token.json — OAuth2 token created after first run
- .env — optional environment variables
- youtube_analytics_output.json — analytics script output
- yt/ — included virtualenv (optional)

## Prerequisites
- Python 3.8+
- A Google Cloud project with YouTube Data API v3 enabled.
- OAuth 2.0 Client Credentials (client.json).

## Get client.json (OAuth 2.0 credentials)
1. Open Google Cloud Console: https://console.cloud.google.com/
2. Create or select a project.
3. Enable the YouTube Data API v3 (APIs & Services → Library → search "YouTube Data API v3" → Enable).
4. Configure OAuth consent screen (External or Internal as appropriate).
5. Create credentials:
   - APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Application type: "Desktop app"
   - Name it and create.
6. Download the JSON credential file and save it to the repository root as `client.json`.

## token.json (how it's created / re-created)
- token.json is generated automatically on first run of upload.py or analytics.py when the app performs OAuth. A browser window will open to authorize the app; after successful authorization token.json will be written to the repo root.
- To force re-authorization, delete token.json and re-run a script.

## Setup (Windows)
1. Open PowerShell and change to repo folder:
```powershell
cd "d:\Sudarshan Khot\Coding\GenAI-Exchange\Youtube-Uploader"
```
2. Create a fresh venv:
```powershell
python -m venv .venv
.venv\Scripts\Activate
```
3. Install dependencies:
```powershell
pip install -r requirements.txt
```

## How to run
- Upload a video (basic):
```powershell
python upload.py
```
- Fetch analytics:
```powershell
python analytics.py
```

Notes:
- On first run you will be prompted to authorize via browser; token.json will be saved locally.
- See the top of upload.py and analytics.py for any CLI arguments or configuration options (title, description, privacy, file path, date ranges for analytics).
- If a script fails, check the terminal output for errors and ensure client.json is correct and API is enabled.

## Troubleshooting
- Invalid client.json or disabled API → enable API and re-download client.json.
- Re-authorize by deleting token.json and re-running.
- For network or TLS errors, ensure system time is correct and certificates are up-to-date.
