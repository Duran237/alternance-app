import random
import time

# { email: (code, expires_at) }
_store: dict[str, tuple[str, float]] = {}
OTP_TTL = 600  # 10 minutes


def generate_otp(email: str) -> str:
    code = f"{random.randint(0, 999999):06d}"
    _store[email] = (code, time.time() + OTP_TTL)
    return code


def verify_otp(email: str, code: str) -> bool:
    entry = _store.get(email)
    if not entry:
        return False
    stored_code, expires_at = entry
    if time.time() > expires_at:
        _store.pop(email, None)
        return False
    if stored_code != code.strip():
        return False
    _store.pop(email, None)
    return True
