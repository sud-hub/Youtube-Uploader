import os
import json
import datetime
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from dotenv import load_dotenv

# Load .env variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URIS)
load_dotenv()

# Scopes for YouTube Data + Analytics
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

TOKEN_FILE = "token.json"


def get_authenticated_services():
    """Handles user authentication and returns API service objects."""
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                print(f"Error refreshing token: {e}. Deleting token and re-authenticating.")
                os.remove(TOKEN_FILE)
                creds = None # Force re-authentication
        
        if not creds: # This block will run if creds are None from the start or after a failed refresh
            redirect_uris = os.getenv("GOOGLE_REDIRECT_URIS", "").split(",")
            client_config = {
                "installed": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "redirect_uris": redirect_uris,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
                client_config, SCOPES
            )
            # Force refresh_token to be returned for offline access
            creds = flow.run_local_server(
                port=8080, access_type="offline", prompt="consent"
            )

            # Save new token (with refresh_token)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

    youtube_data = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    youtube_analytics = googleapiclient.discovery.build("youtubeAnalytics", "v2", credentials=creds)
    return youtube_data, youtube_analytics


def get_channel_info(youtube_data):
    """Fetches basic channel information."""
    request = youtube_data.channels().list(
        part="snippet,statistics,contentDetails,brandingSettings",
        mine=True
    )
    response = request.execute()
    if not response.get("items"):
        raise Exception("No channel found for the authenticated user.")
    return response["items"][0]


def get_channel_analytics(youtube_analytics, start_date, end_date, metrics, dimensions=None, filters=None, sort=None):
    """Fetches analytics data for the channel."""
    request = youtube_analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics=metrics,
        dimensions=dimensions,
        filters=filters,
        sort=sort
    )
    return request.execute()


def main():
    """Main function to fetch and save YouTube data."""
    youtube_data, youtube_analytics = get_authenticated_services()
    
    # This dictionary will hold all the data to be saved.
    output_data = {}

    # 1. Basic channel info
    channel_info_response = get_channel_info(youtube_data)
    output_data['channel_info'] = channel_info_response
    
    print("Channel Title:", channel_info_response["snippet"]["title"])
    print("Subscribers:", channel_info_response["statistics"].get("subscriberCount"))
    print("Total Views:", channel_info_response["statistics"].get("viewCount"))
    print("Video Count:", channel_info_response["statistics"].get("videoCount"))

    # 2. Analytics last 30 days
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)
    analytics_response = get_channel_analytics(
        youtube_analytics,
        start_date=thirty_days_ago.isoformat(),
        end_date=today.isoformat(),
        metrics="views,likes,subscribersGained,estimatedMinutesWatched",
        dimensions="day",
        sort="day"
    )
    output_data['daily_analytics'] = analytics_response
    
    print("\nAnalytics Data for last 30 days:")
    for col in analytics_response.get("columnHeaders", []):
        print(col["name"], end="\t")
    print()
    for row in analytics_response.get("rows", []):
        print("\t".join(str(x) for x in row))

    # 3. Analytics per video (latest 5)
    videos_req = youtube_data.search().list(
        part="id",
        forMine=True,
        type="video",
        order="date",
        maxResults=5
    )
    videos_resp = videos_req.execute()
    video_ids = [item["id"].get("videoId") for item in videos_resp.get("items", []) if item["id"].get("videoId")]

    if video_ids:
        filters = "video==" + ",".join(video_ids)
        analytics_per_video = get_channel_analytics(
            youtube_analytics,
            start_date=thirty_days_ago.isoformat(),
            end_date=today.isoformat(),
            metrics="views,likes,subscribersGained,estimatedMinutesWatched",
            dimensions="video",
            filters=filters,
            sort="-views"
        )
        output_data['video_analytics'] = analytics_per_video
        
        print("\nAnalytics per video (latest 5):")
        for col in analytics_per_video.get("columnHeaders", []):
            print(col["name"], end="\t")
        print()
        for row in analytics_per_video.get("rows", []):
            print("\t".join(str(x) for x in row))
    else:
        print("\nNo recent videos found.")
        output_data['video_analytics'] = {}


    # 4. Save the combined output to a JSON file
    output_filename = "youtube_analytics_output.json"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Successfully saved all data to {output_filename}")
    except Exception as e:
        print(f"\n❌ Error saving data to file: {e}")


if __name__ == "__main__":
    main()

