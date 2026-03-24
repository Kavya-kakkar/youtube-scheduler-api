from fastapi import FastAPI, UploadFile, File, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import requests
import os
import shutil
import json

from scheduler import check_and_upload_videos
from google_drive_uploader import upload_to_drive
import models
from database import engine, Base, SessionLocal

app = FastAPI()
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# ==============================
# OAuth Settings
# ==============================
CLIENT_SECRET_FILE = "client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.file"
]

# 👉 IMPORTANT: change for local vs render
REDIRECT_URI = "http://127.0.0.1:8000/auth/callback"
# For Render use:
# REDIRECT_URI = "https://youtube-scheduler-api.onrender.com/auth/callback"

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
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload to Google Drive
    drive_file_id = upload_to_drive(file_location)

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
    with open(CLIENT_SECRET_FILE, "r") as f:
        client_config = json.load(f)["web"]

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"

    params = {
        "client_id": client_config["client_id"],
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }

    request_url = requests.Request("GET", auth_url, params=params).prepare().url

    return RedirectResponse(request_url)

# ==============================
# OAuth Callback
# ==============================
@app.get("/auth/callback")
def auth_callback(request: Request):
    code = request.query_params.get("code")

    if not code:
        return {"error": "No code received"}

    with open(CLIENT_SECRET_FILE, "r") as f:
        client_config = json.load(f)["web"]

    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": client_config["client_id"],
        "client_secret": client_config["client_secret"],
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=data)
    token_data = response.json()

    if "access_token" not in token_data:
        return {"error": token_data}
    
    formatted_token = {
    "token": token_data.get("access_token"),
    "refresh_token": token_data.get("refresh_token"),
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": client_config["client_id"],
    "client_secret": client_config["client_secret"],
    "scopes": SCOPES
    }
    with open("youtube_token.json", "w") as f:
        json.dump(formatted_token, f)

    return {"message": "Authentication successful ✅"}

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

# ==============================
# Upload Now
# ==============================
@app.post("/upload-now/{video_id}")
def upload_now(video_id: int, db: Session = Depends(get_db)):
    video = db.query(models.Video).filter(models.Video.id == video_id).first()

    if not video:
        return {"error": "Video not found"}

    try:
        check_and_upload_videos()
        return {"message": f"Upload triggered for video {video_id}"}
    except Exception as e:
        return {"error": str(e)}

# ==============================
# Run Scheduler
# ==============================
@app.get("/run-scheduler")
def run_scheduler():
    print("🔁 Manual scheduler triggered")
    check_and_upload_videos()
    return {"message": "Scheduler executed - check logs"}