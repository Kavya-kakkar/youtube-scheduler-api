from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil

from scheduler import start_scheduler
from google_drive_uploader import upload_to_drive

import models
from database import engine, Base, SessionLocal

app = FastAPI()

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

# Create uploads folder if not exists
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Dependency: Get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/upload")
def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    tags: str = Form(...),
    scheduled_time: str = Form(...),
    repeat_weekly: bool = Form(False),
    is_short: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # Convert scheduled_time → datetime
    scheduled_datetime = datetime.fromisoformat(scheduled_time)

    # Save file locally first
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload file to Google Drive
    drive_file_id = upload_to_drive(file_location)

    # Save video record in database
    new_video = models.Video(
        title=title,
        description=description,
        tags=tags,
        file_path=drive_file_id,  # Save Drive file ID
        scheduled_time=scheduled_datetime,
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
        "is_short": new_video.is_short,
        "status": new_video.status
    }