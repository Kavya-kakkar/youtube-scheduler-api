import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

TOKEN_FILE = "youtube_token.json"
CLIENT_SECRET_FILE = "client_secret.json"

# ------------------------
# Authenticate and build Drive service
# ------------------------
def authenticate_drive():
    if not os.path.exists(TOKEN_FILE):
        raise Exception("User not authenticated. Please login first.")

    # Load token
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    # Load client secrets
    with open(CLIENT_SECRET_FILE) as f:
        client_config = json.load(f)["web"]

    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_config["client_id"],
        client_secret=client_config["client_secret"],
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/youtube.upload"
        ]
    )

    # ✅ Auto refresh token if expired
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())

        # Save updated token
        with open(TOKEN_FILE, "w") as f:
            json.dump({
                "access_token": creds.token,
                "refresh_token": creds.refresh_token
            }, f)

    drive_service = build("drive", "v3", credentials=creds)
    return drive_service


# ------------------------
# Download file from Drive
# ------------------------
def download_from_drive(file_id, output_path):
    drive_service = authenticate_drive()

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