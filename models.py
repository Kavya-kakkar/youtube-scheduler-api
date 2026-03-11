from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    tags = Column(String)
    file_path = Column(String)
    scheduled_time = Column(DateTime)
    repeat_weekly = Column(Boolean)
    status = Column(String)
    is_short = Column(Boolean, default=False)