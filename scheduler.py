from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sqlalchemy.orm import Session
import os

from database import SessionLocal
import models

from youtube_uploader import upload_video_to_youtube
from google_drive_uploader import download_from_drive


def check_and_upload_videos():

    db: Session = SessionLocal()

    videos = db.query(models.Video).filter(
        models.Video.status == "Pending",
        models.Video.scheduled_time <= datetime.now()
    ).all()

    for video in videos:

        try:
            print(f"Uploading video ID {video.id}...")

            # temp file location
            local_file = f"uploads/temp_{video.id}.mp4"

            # download from Google Drive
            download_from_drive(video.file_path, local_file)

            print("Downloaded file from Google Drive")

            # upload to YouTube
            upload_video_to_youtube(
                video.title,
                video.description,
                video.tags,
                local_file,
                video.is_short
            )

            # update status
            video.status = "Uploaded"
            db.commit()

            print("Upload successful")

            # delete temp file after upload
            if os.path.exists(local_file):
                os.remove(local_file)

        except Exception as e:
            print(f"Error uploading video ID {video.id}: {e}")

    db.close()


def start_scheduler():

    # 🔹 CLEAN OLD TEMP FILES WHEN SERVER STARTS
    if os.path.exists("uploads"):
        for f in os.listdir("uploads"):
            if f.startswith("temp_"):
                os.remove(os.path.join("uploads", f))

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_and_upload_videos,
        "interval",
        minutes=1,
        max_instances=1
    )

    scheduler.start()