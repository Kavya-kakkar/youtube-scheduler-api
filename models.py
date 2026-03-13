from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    description = Column(Text)

    tags = Column(String)

    file_path = Column(String, nullable=False)

    privacy_status = Column(String, default="private")

    scheduled_time = Column(DateTime, nullable=False)

    repeat_weekly = Column(Boolean, default=False)

    status = Column(String, default="Pending")

    is_short = Column(Boolean, default=False)