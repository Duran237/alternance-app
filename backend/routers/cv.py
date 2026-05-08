import os
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.user import User
from utils.cv_parser import parse_cv
from utils.security import get_current_user
from services.ai_service import analyze_cv

router = APIRouter(prefix="/cv", tags=["cv"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

    filename = f"cv_{current_user.id}.pdf"
    save_path = UPLOAD_DIR / filename

    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    parsed = parse_cv(str(save_path))

    current_user.cv_path = str(save_path)
    current_user.cv_text = parsed["text"]

    # Mise à jour basique depuis le parsing PDF
    if parsed["skills"]:
        existing = set(current_user.skills or [])
        current_user.skills = list(existing | set(parsed["skills"]))
    if parsed["github"] and not current_user.github_url:
        current_user.github_url = parsed["github"]
    if parsed["linkedin"] and not current_user.linkedin_url:
        current_user.linkedin_url = parsed["linkedin"]
    if parsed["phone"] and not current_user.phone:
        current_user.phone = parsed["phone"]

    # Analyse IA approfondie pour enrichir le profil
    try:
        ai_result = await analyze_cv(parsed["text"])
        if isinstance(ai_result, dict):
            # Fusionner les compétences IA avec celles déjà détectées
            ai_skills = ai_result.get("skills", [])
            if ai_skills:
                current_skills = set(current_user.skills or [])
                current_user.skills = list(current_skills | set(ai_skills))

            # Rôles cibles suggérés par l'IA
            ai_roles = ai_result.get("target_roles", [])
            if ai_roles and not current_user.target_roles:
                current_user.target_roles = ai_roles

            # Téléphone si pas déjà renseigné
            ai_phone = ai_result.get("phone")
            if ai_phone and not current_user.phone:
                current_user.phone = ai_phone
    except Exception:
        pass  # L'analyse IA est optionnelle, on continue sans elle

    db.add(current_user)
    await db.commit()

    return {
        "message": "CV uploadé et profil mis à jour",
        "skills_detected": current_user.skills,
        "target_roles": current_user.target_roles,
        "phone": current_user.phone,
    }


@router.get("/download")
async def download_cv(current_user: User = Depends(get_current_user)):
    if not current_user.cv_path or not Path(current_user.cv_path).exists():
        raise HTTPException(status_code=404, detail="Aucun CV trouvé")
    return FileResponse(current_user.cv_path, media_type="application/pdf", filename="mon_cv.pdf")


@router.post("/analyze")
async def analyze_cv_endpoint(current_user: User = Depends(get_current_user)):
    if not current_user.cv_text:
        raise HTTPException(status_code=400, detail="Uploadez d'abord votre CV")
    result = await analyze_cv(current_user.cv_text)
    return result
