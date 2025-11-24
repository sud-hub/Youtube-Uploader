import os
import json
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

# OAuth scopes: here it's for uploading videos
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

TOKEN_FILE = "token.json"

def authenticate_youtube():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            redirect_uris = os.getenv("GOOGLE_REDIRECT_URIS", "").split(",")
            client_config = {
                "installed": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "redirect_uris": redirect_uris,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }

            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
                client_config, SCOPES
            )
            # 👇 Force Google to ask again and issue refresh_token with correct scopes
            creds = flow.run_local_server(port=8080, access_type="offline", prompt="consent")

        # Save new token
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    return youtube

def upload_video(youtube):
    request_body = {
        "snippet": {
            "categoryId": "22",
            "title": "Uploaded from Python",
            "description": "This is the most awesome description ever",
            "tags": ["test", "python", "api"]
        },
        "status": {
            "privacyStatus": "private"
        }
    }

    media_file = "generated_video.mp4"

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=googleapiclient.http.MediaFileUpload(media_file, chunksize=-1, resumable=True)
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload {int(status.progress() * 100)}%")
    print(f"Video uploaded with ID: {response['id']}")

if __name__ == "__main__":
    youtube = authenticate_youtube()
    upload_video(youtube)
