import os
import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

TOKEN_FILE = "token.json"


def authenticate_drive():
    creds = None

    # Load token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)

    # If not logged in
    if not creds:
        raise Exception("User not authenticated. Please login first.")

    # Refresh token if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    drive_service = build("drive", "v3", credentials=creds)

    return drive_service


# Upload file to Google Drive
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

    print("Uploaded to Google Drive:", file.get("id"))

    return file.get("id")


# Download file from Google Drive
def download_from_drive(file_id, destination):
    drive_service = authenticate_drive()

    request = drive_service.files().get_media(fileId=file_id)

    fh = io.FileIO(destination, "wb")

    downloader = MediaIoBaseDownload(fh, request)

    done = False

    while not done:
        status, done = downloader.next_chunk()

    print("Downloaded file from Google Drive")