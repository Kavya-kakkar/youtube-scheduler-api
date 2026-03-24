import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.json"


# =========================
# Authenticate YouTube
# =========================
def authenticate_youtube():
    creds = None

    # ✅ Load token safely
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as token:
                token_data = json.load(token)

                creds = Credentials.from_authorized_user_info(
                    token_data, SCOPES
                )
        except Exception as e:
            print("❌ Invalid token format. Please login again.")
            raise Exception("Invalid token. Delete youtube_token.json and login again.")

    # ✅ Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())

            # Save refreshed token
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        except Exception as e:
            print("❌ Token refresh failed:", str(e))
            raise Exception("Token expired. Please login again.")

    # ❌ If no credentials
    if not creds or not creds.valid:
        raise Exception("❌ No valid credentials found. Please login first.")

    # ✅ Build YouTube service
    youtube = build("youtube", "v3", credentials=creds)
    return youtube


# =========================
# Upload Video
# =========================
def upload_video_to_youtube(
    title,
    description,
    tags,
    file_path,
    privacy_status="private",
    publish_time=None,
):
    youtube = authenticate_youtube()

    # ✅ Clean inputs
    title = str(title)
    description = str(description)
    privacy_status = str(privacy_status or "private")

    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    # ✅ Request body
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": privacy_status
        },
    }

    # ✅ Scheduled publishing (IMPORTANT FIX)
    if publish_time:
        request_body["status"]["publishAt"] = publish_time
        request_body["status"]["privacyStatus"] = "private"

    # ✅ Upload file
    media_file = MediaFileUpload(file_path, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )

    response = request.execute()

    print("✅ Video uploaded successfully to YouTube")
    return response.get("id")