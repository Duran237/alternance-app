from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from database import Base


class NightReport(Base):
    __tablename__ = "night_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    run_at = Column(DateTime, default=datetime.utcnow)
    new_jobs_found = Column(Integer, default=0)
    compatible_jobs = Column(Integer, default=0)
    drafts_prepared = Column(Integer, default=0)
    keywords_used = Column(String, nullable=True)
    top_jobs = Column(JSON, default=list)

    user = relationship("User")
