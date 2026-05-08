import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from database import get_db
from models.user import User
from services.email_service import send_otp_email, send_welcome_email
from services.otp_service import generate_otp, verify_otp
from utils.security import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    is_email_verified: bool = False


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        skills=[],
        target_roles=[],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})

    # Envoi OTP de vérification
    try:
        otp = generate_otp(user.email)
        send_otp_email(to_email=user.email, user_name=user.name, otp_code=otp)
    except Exception as e:
        logger.error(f"[Auth] Erreur envoi OTP register : {e}")

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        is_email_verified=False,
    )


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        is_email_verified=bool(user.is_email_verified),
    )


@router.post("/verify-email")
async def verify_email(data: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    if not verify_otp(data.email, data.code):
        raise HTTPException(status_code=400, detail="Code invalide ou expiré")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.is_email_verified = 1
    db.add(user)
    await db.commit()

    try:
        send_welcome_email(to_email=user.email, user_name=user.name)
    except Exception:
        pass

    return {"message": "Email vérifié avec succès"}


@router.post("/resend-otp")
async def resend_otp(data: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    try:
        otp = generate_otp(user.email)
        send_otp_email(to_email=user.email, user_name=user.name, otp_code=otp)
    except Exception:
        pass
    return {"message": "Code renvoyé"}


@router.post("/forgot-password")
async def forgot_password(data: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    # Toujours répondre OK pour ne pas révéler si l'email existe
    if user:
        try:
            otp = generate_otp(user.email)
            send_otp_email(to_email=user.email, user_name=user.name, otp_code=otp)
        except Exception as e:
            logger.error(f"[Auth] Erreur envoi OTP forgot-password : {e}")
    return {"message": "Si cet email existe, un code a été envoyé"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (8 caractères minimum)")
    if not verify_otp(data.email, data.code):
        raise HTTPException(status_code=400, detail="Code invalide ou expiré")
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.password_hash = hash_password(data.new_password)
    db.add(user)
    await db.commit()
    return {"message": "Mot de passe réinitialisé"}
