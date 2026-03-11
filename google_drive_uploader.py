import os
import pickle
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def authenticate_drive():
    creds = None

    if os.path.exists("drive_token.pickle"):
        with open("drive_token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("drive_token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


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

    while done is False:
        status, done = downloader.next_chunk()

    print("Downloaded file from Google Drive")