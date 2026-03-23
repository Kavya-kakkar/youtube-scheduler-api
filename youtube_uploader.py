import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

TOKEN_FILE = "youtube_token.json"


def authenticate_youtube():
    creds = None

    # Load saved token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as token:
            creds = Credentials.from_authorized_user_info(
                json.load(token), SCOPES
            )

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

        # Save updated token
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    if not creds:
        raise Exception("❌ No valid credentials found. Please login first.")

    youtube = build("youtube", "v3", credentials=creds)

    return youtube


def upload_video_to_youtube(
    title,
    description,
    tags,
    file_path,
    privacy_status="private",
    publish_time=None,
):
    youtube = authenticate_youtube()

    # Ensure correct types
    title = str(title)
    description = str(description)
    privacy_status = str(privacy_status)

    if isinstance(tags, str):
        tags = tags.split(",")

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": privacy_status
        },
    }

    # Scheduled publishing
    if publish_time:
        request_body["status"]["publishAt"] = publish_time

    media_file = MediaFileUpload(file_path)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )

    response = request.execute()

    print("✅ Video uploaded successfully.")
    return response["id"]