from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog

from ....core.database import get_db
from ....core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    validate_arabic_password,
    get_password_hash
)
from ....core.auth_dependency import get_current_user
from ....core.audit import log_audit_event
from ....core.rate_limit import limiter
from ....models.user import User
from ....schemas.auth import (
    TokenResponse,
    UserLogin,
    UserRegister,
    PasswordReset,
    PasswordChange
)

logger = structlog.get_logger()
router = APIRouter()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """User login with Arabic support"""
    try:
        # Find user by email or username
        user = db.query(User).filter(
            (User.email == user_credentials.email_or_username) |
            (User.username == user_credentials.email_or_username)
        ).first()
        
        if not user:
            logger.warning("Login attempt with invalid credentials", email=user_credentials.email_or_username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="البريد الإلكتروني أو كلمة المرور غير صحيحة"
            )
        
        if not verify_password(user_credentials.password, user.password_hash):
            logger.warning("Login attempt with wrong password", user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="البريد الإلكتروني أو كلمة المرور غير صحيحة"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="الحساب غير مفعل"
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        logger.info("User logged in successfully", user_id=user.id)
        log_audit_event(
            event_type="auth.login.success",
            user_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            metadata={"login_identifier": user_credentials.email_or_username},
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name_ar": user.full_name_ar,
                "full_name_en": user.full_name_en,
                "role": user.role,
                "language_preference": user.language_preference
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في تسجيل الدخول"
        )


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """User registration with Arabic password validation"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="البريد الإلكتروني مستخدم بالفعل"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="اسم المستخدم مستخدم بالفعل"
                )
        
        # Validate password
        password_validation = validate_arabic_password(user_data.password)
        if not password_validation['is_valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="كلمة المرور لا تستوفي المتطلبات",
                headers={"X-Password-Errors": str(password_validation['errors'])}
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name_ar=user_data.full_name_ar,
            full_name_en=user_data.full_name_en,
            password_hash=hashed_password,
            language_preference=user_data.language_preference or "ar",
            timezone=user_data.timezone or "Asia/Riyadh"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(new_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
        
        logger.info("User registered successfully", user_id=new_user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(new_user.id),
                "email": new_user.email,
                "username": new_user.username,
                "full_name_ar": new_user.full_name_ar,
                "full_name_en": new_user.full_name_en,
                "role": new_user.role,
                "language_preference": new_user.language_preference
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في إنشاء الحساب"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Refresh access token"""
    try:
        from ....core.security import verify_token
        
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="رمز التحديث غير صحيح"
            )
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="المستخدم غير موجود أو غير مفعل"
            )
        
        # Create new tokens
        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في تحديث الرمز"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """User logout"""
    try:
        # In a real implementation, you might want to blacklist the token
        logger.info("User logged out", user_id=current_user.id)
        return {"message": "تم تسجيل الخروج بنجاح"}
        
    except Exception as e:
        logger.error("Logout error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في تسجيل الخروج"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Change user password with Arabic validation"""
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="كلمة المرور الحالية غير صحيحة"
            )
        
        # Validate new password
        password_validation = validate_arabic_password(password_data.new_password)
        if not password_validation['is_valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="كلمة المرور الجديدة لا تستوفي المتطلبات",
                headers={"X-Password-Errors": str(password_validation['errors'])}
            )
        
        # Update password
        user.password_hash = get_password_hash(password_data.new_password)
        db.commit()
        
        logger.info("Password changed successfully", user_id=user.id)
        return {"message": "تم تغيير كلمة المرور بنجاح"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في تغيير كلمة المرور"
        )


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Request password reset"""
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # In a real implementation, send reset email
            logger.info("Password reset requested", user_id=user.id)
        
        # Always return success to prevent email enumeration
        return {"message": "إذا كان البريد الإلكتروني مسجل، سيتم إرسال رابط إعادة تعيين كلمة المرور"}
        
    except Exception as e:
        logger.error("Forgot password error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في طلب إعادة تعيين كلمة المرور"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current user information"""
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name_ar": user.full_name_ar,
            "full_name_en": user.full_name_en,
            "role": user.role,
            "language_preference": user.language_preference,
            "timezone": user.timezone,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
    except Exception as e:
        logger.error("Get user info error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في جلب معلومات المستخدم"
        ) 
