import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def authenticate_youtube():
    creds = None

    if os.path.exists("youtube_token.pickle"):
        with open("youtube_token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("youtube_token.pickle", "wb") as token:
            pickle.dump(creds, token)

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

    # Ensure values are correct types
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

    # For scheduled publishing
    if publish_time:
        request_body["status"]["publishAt"] = publish_time

    media_file = MediaFileUpload(file_path)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )

    response = request.execute()

    print("Video uploaded successfully.")
    return response["id"]