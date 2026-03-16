from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil
import pickle

from google_auth_oauthlib.flow import Flow

from scheduler import start_scheduler
from google_drive_uploader import upload_to_drive

import models
from database import engine, Base, SessionLocal


app = FastAPI()

# OAuth settings
CLIENT_SECRET_FILE = "client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.file"
]

REDIRECT_URI = "http://localhost:8000/auth/callback"

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Start scheduler
start_scheduler()

# Upload folder
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Upload + schedule video
@app.post("/upload")
def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    tags: str = Form(...),
    scheduled_time: datetime = Form(...),
    repeat_weekly: bool = Form(False),
    is_short: bool = Form(False),
    privacy_status: str = Form("private"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # Save file locally
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload to Google Drive
    drive_file_id = upload_to_drive(file_location)

    # Save video info in database
    new_video = models.Video(
        title=title,
        description=description,
        tags=tags,
        file_path=drive_file_id,
        privacy_status=privacy_status,
        scheduled_time=scheduled_time,
        repeat_weekly=repeat_weekly,
        status="Pending",
        is_short=is_short
    )

    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    return {
        "message": "Video scheduled successfully",
        "video_id": new_video.id,
        "google_drive_file_id": drive_file_id,
        "status": new_video.status
    }


# Google OAuth login
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.file"
]

@app.get("/login")
def login():
    flow = Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/callback"
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )

    return RedirectResponse(authorization_url)


# OAuth callback
@app.get("/auth/callback")
def auth_callback(code: str):

    flow = Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/callback"
    )

    flow.fetch_token(code=code)

    credentials = flow.credentials

    with open("youtube_token.json", "w") as token:
        token.write(credentials.to_json())

    return {"message": "Authentication successful"}

@app.get("/videos")
def get_all_videos(db: Session = Depends(get_db)):

    videos = db.query(models.Video).all()

    return [
        {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "tags": video.tags,
            "privacy_status": video.privacy_status,
            "scheduled_time": video.scheduled_time,
            "status": video.status,
            "is_short": video.is_short
        }
        for video in videos
    ]