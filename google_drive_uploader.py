import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

TOKEN_FILE = "youtube_token.json"

# ------------------------
# Authenticate and build Drive service
# ------------------------
def authenticate_drive():
    if not os.path.exists(TOKEN_FILE):
        raise Exception("User not authenticated. Please login first.")

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/youtube.upload"
        ]
    )

    # ✅ Build the actual Drive service using the credentials
    drive_service = build("drive", "v3", credentials=creds)
    return drive_service


# ------------------------
# Download file from Drive
# ------------------------
def download_from_drive(file_id, output_path):
    creds = authenticate_drive()
    drive_service = build("drive", "v3", credentials=creds)

    request = drive_service.files().get_media(fileId=file_id)
    file_data = request.execute()

    with open(output_path, "wb") as f:
        f.write(file_data)

    return output_path


# ------------------------
# Upload file to Drive
# ------------------------
def upload_to_drive(file_path):
    drive_service = authenticate_drive()

    file_metadata = {
        "name": os.path.basename(file_path)
    }

    media = MediaFileUpload(file_path, resumable=True)

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return file.get("id")