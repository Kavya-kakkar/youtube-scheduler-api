from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import os

from database import SessionLocal
import models

from youtube_uploader import upload_video_to_youtube
from google_drive_uploader import download_from_drive

def check_and_upload_videos():

    db: Session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)  # ✅ timezone safe

        videos = db.query(models.Video).filter(
            models.Video.status == "Pending",
            models.Video.scheduled_time <= now
        ).all()

        for video in videos:

            try:
                print(f"🚀 Uploading video ID {video.id}...")

                # temp file
                local_file = f"uploads/temp_{video.id}.mp4"

                # download from Google Drive
                download_from_drive(video.file_path, local_file)
                print("✅ Downloaded from Google Drive")

                # YouTube requires RFC3339 format
                publish_time = video.scheduled_time.astimezone(timezone.utc).isoformat()

                # upload to YouTube
                video_id = upload_video_to_youtube(
                    title=str(video.title),
                    description=str(video.description),
                    tags=str(video.tags),
                    file_path=local_file,
                    privacy_status=str(video.privacy_status),
                    publish_time=None
                )

                print(f"✅ Uploaded successfully. YouTube ID: {video_id}")
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"🎉 Video uploaded! Watch it here: {youtube_url}")

                # update DB
                video.status = "Uploaded"
                db.commit()

                # cleanup
                if os.path.exists(local_file):
                    os.remove(local_file)

            except Exception as e:
                print(f"❌ Error uploading video ID {video.id}: {e}")

                # optional: mark as failed
                video.status = "Failed"
                db.commit()

    finally:
        db.close()


def start_scheduler():

    # clean old temp files
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
        trigger="interval",
        minutes=1,
        max_instances=1,   # ✅ prevent duplicate uploads
        replace_existing=True
    )

    scheduler.start()

    print(" YouTube scheduler started...")