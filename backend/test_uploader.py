from youtube_uploader import upload_video_to_youtube

video_id = upload_video_to_youtube(
    title="Test Upload From Python",
    description="This is a test upload from my YouTube Scheduler",
    tags="python,automation,test",
    file_path="uploads/Screen Recording 2026-03-07 184611.mp4"
)

print("Uploaded Video ID:", video_id)