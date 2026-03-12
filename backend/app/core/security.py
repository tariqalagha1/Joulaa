from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import re
import bcrypt
import arabic_reshaper
from bidi.algorithm import get_display

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()

# Arabic password validation patterns
ARABIC_PATTERNS = {
    'arabic_chars': r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]',
    'english_chars': r'[a-zA-Z]',
    'numbers': r'[0-9]',
    'special_chars': r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]'
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback for passlib/bcrypt backend compatibility issues.
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    try:
        return pwd_context.hash(password)
    except Exception:
        # Fallback for passlib/bcrypt backend compatibility issues.
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def validate_arabic_password(password: str) -> dict:
    """
    Validate password with Arabic-specific requirements
    Returns dict with validation results and Arabic-specific feedback
    """
    errors = []
    warnings = []
    
    # Check minimum length
    if len(password) < 8:
        errors.append("كلمة المرور يجب أن تكون 8 أحرف على الأقل")
    
    # Check for Arabic characters
    arabic_chars = re.findall(ARABIC_PATTERNS['arabic_chars'], password)
    if arabic_chars:
        warnings.append("يُنصح بعدم استخدام الأحرف العربية في كلمة المرور")
    
    # Check for mixed character types
    has_english = bool(re.search(ARABIC_PATTERNS['english_chars'], password))
    has_numbers = bool(re.search(ARABIC_PATTERNS['numbers'], password))
    has_special = bool(re.search(ARABIC_PATTERNS['special_chars'], password))
    
    if not (has_english and has_numbers):
        errors.append("كلمة المرور يجب أن تحتوي على أحرف إنجليزية وأرقام")
    
    if not has_special:
        warnings.append("يُنصح بإضافة رموز خاصة لزيادة الأمان")
    
    # Check for common patterns
    common_patterns = ['123456', 'password', 'qwerty', 'admin', 'كلمة', 'مرور']
    for pattern in common_patterns:
        if pattern.lower() in password.lower():
            errors.append(f"لا تستخدم '{pattern}' في كلمة المرور")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'strength_score': calculate_password_strength(password)
    }


def calculate_password_strength(password: str) -> int:
    """Calculate password strength score (0-100)"""
    score = 0
    
    # Length contribution
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    
    # Character variety contribution
    if re.search(ARABIC_PATTERNS['english_chars'], password):
        score += 20
    if re.search(ARABIC_PATTERNS['numbers'], password):
        score += 20
    if re.search(ARABIC_PATTERNS['special_chars'], password):
        score += 20
    
    # Mixed case
    if re.search(r'[a-z]', password) and re.search(r'[A-Z]', password):
        score += 10
    
    return min(score, 100)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"user_id": user_id, "payload": payload}


def format_arabic_text(text: str) -> str:
    """Format Arabic text for proper RTL display"""
    if not text:
        return text
    
    # Reshape Arabic text
    reshaped_text = arabic_reshaper.reshape(text)
    
    # Apply bidirectional algorithm
    formatted_text = get_display(reshaped_text)
    
    return formatted_text


def sanitize_arabic_input(text: str) -> str:
    """Sanitize Arabic text input"""
    if not text:
        return text
    
    # Remove potentially dangerous characters while preserving Arabic
    # Allow Arabic characters, English, numbers, and basic punctuation
    allowed_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z0-9\s\-_.,!?()\[\]{}:;\'"`~@#$%^&*+=|\\/<>]'
    
    sanitized = re.sub(f'[^{allowed_pattern}]', '', text)
    
    # Limit length
    if len(sanitized) > 10000:  # 10KB limit
        sanitized = sanitized[:10000]
    
    return sanitized.strip()


def generate_secure_random_string(length: int = 32) -> str:
    """Generate secure random string for tokens"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage"""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()


# Rate limiting utilities
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """Check if request is rate limited"""
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window)
        return current > limit
    
    async def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for a key"""
        current = await self.redis.get(key)
        return int(current) if current else 0 
