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

    try:
        videos = db.query(models.Video).filter(
            models.Video.status == "Pending",
            models.Video.scheduled_time <= datetime.now()
        ).all()

        for video in videos:

            try:
                print(f"Uploading video ID {video.id}...")

                # temporary file path
                local_file = f"uploads/temp_{video.id}.mp4"

                # download video from Google Drive
                download_from_drive(video.file_path, local_file)

                print("Downloaded file from Google Drive")

                # convert publish time to ISO format
                publish_time = video.scheduled_time.isoformat() + "Z"

                # upload to YouTube
                video_id = upload_video_to_youtube(
                    str(video.title),
                    str(video.description),
                    str(video.tags),
                    local_file,
                    str(video.privacy_status),
                    publish_time
                )

                print(f"Video uploaded successfully. ID: {video_id}")

                # update database status
                video.status = "Uploaded"
                db.commit()

                # delete temporary file
                if os.path.exists(local_file):
                    os.remove(local_file)

            except Exception as e:
                print(f"Error uploading video ID {video.id}: {e}")

    finally:
        db.close()


def start_scheduler():

    # clean old temp files when server starts
    if os.path.exists("uploads"):
        for f in os.listdir("uploads"):
            if f.startswith("temp_"):
                try:
                    os.remove(os.path.join("uploads", f))
                except:
                    pass

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_and_upload_videos,
        "interval",
        minutes=1,
        max_instances=3,
        replace_existing=True
    )

    scheduler.start()

    print("YouTube scheduler started...")