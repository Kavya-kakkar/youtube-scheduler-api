from fastapi import FastAPI, UploadFile, File, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil

from google_auth_oauthlib.flow import Flow
from scheduler import start_scheduler
from google_drive_uploader import upload_to_drive
import models
from database import engine, Base, SessionLocal


app = FastAPI()
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
# ==============================
# OAuth settings
# ==============================
CLIENT_SECRET_FILE = "client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.file"
]

REDIRECT_URI = "https://youtube-scheduler-api.onrender.com/auth/callback"

# ==============================
# CORS
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Database
# ==============================
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================
# Scheduler
# ==============================
start_scheduler()

# ==============================
# Upload folder
# ==============================
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ==============================
# Upload + Schedule Video
# ==============================
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

    file_location = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save file locally
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload to Google Drive
    drive_file_id = upload_to_drive(file_location)

    # Save to DB
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

# ==============================
# Google OAuth Login
# ==============================
@app.get("/login")
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI   # ✅ SAME everywhere
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"   # ensures refresh token
    )

    return RedirectResponse(authorization_url)

# ==============================
# OAuth Callback
# ==============================
@app.get("/auth/callback")
def auth_callback(request: Request):

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI   # ✅ SAME here too
    )

    # Exchange code for token
    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials

    # Save token
    with open("youtube_token.json", "w") as token:
        token.write(credentials.to_json())

    return {
        "message": "Authentication successful",
        "status": "connected to Google"
    }

# ==============================
# Get All Videos
# ==============================
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