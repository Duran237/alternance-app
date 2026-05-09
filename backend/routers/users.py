from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from utils.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    school: Optional[str] = None
    education_level: Optional[str] = None
    skills: List[str] = []
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    cv_path: Optional[str] = None
    target_city: Optional[str] = None
    target_salary: Optional[str] = None
    target_roles: List[str] = []

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    school: Optional[str] = None
    education_level: Optional[str] = None
    skills: Optional[List[str]] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    target_city: Optional[str] = None
    target_salary: Optional[str] = None
    target_roles: Optional[List[str]] = None


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserProfile)
async def update_me(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
