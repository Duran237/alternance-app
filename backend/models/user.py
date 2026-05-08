from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    skills = Column(JSON, default=list)
    github_url = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    is_email_verified = Column(Integer, default=0)
    cv_path = Column(String, nullable=True)
    cv_text = Column(Text, nullable=True)
    target_city = Column(String, nullable=True)
    target_salary = Column(String, nullable=True)
    target_roles = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("Application", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
