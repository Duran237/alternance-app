from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    skills_required = Column(JSON, default=list)
    url = Column(String, unique=True, nullable=False)
    source = Column(String, nullable=True)
    contract_type = Column(String, nullable=True)
    level = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("Application", back_populates="job")
