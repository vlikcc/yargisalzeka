# auth.py - Authentication endpoints
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from loguru import logger

from .security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, get_current_user, TokenData, Token,
    get_client_ip, limiter
)
from .firestore_db import firestore_manager

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    subscription_plan: str
    created_at: str

@router.post("/register", response_model=dict)
@limiter.limit("3/minute")  # Registration rate limit
async def register_user(request: Request, user_data: UserRegister):
    """
    Yeni kullanıcı kaydı
    """
    try:
        client_ip = get_client_ip(request)
        logger.info(f"Kayıt isteği - Email: {user_data.email}, IP: {client_ip}")
        
        # Email validation ve duplicate check
        # Bu kısım database ile entegre edilecek
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Şifre en az 8 karakter olmalıdır"
            )
        
        # Şifreyi hashle
        hashed_password = get_password_hash(user_data.password)
        
        # Firestore'a kullanıcı kaydet ve ücretsiz deneme paketi ata
        user_id = await firestore_manager.create_user_with_trial(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        return {
            "message": "Kullanıcı başarıyla kaydedildi. 5 aramalık ücretsiz deneme paketiniz 3 gün süreyle aktif edildi!",
            "user_id": user_id,
            "email": user_data.email,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kayıt hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kayıt sırasında bir hata oluştu"
        )

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # Login rate limit
async def login_user(request: Request, user_credentials: UserLogin):
    """
    Kullanıcı girişi
    """
    try:
        client_ip = get_client_ip(request)
        logger.info(f"Giriş isteği - Email: {user_credentials.email}, IP: {client_ip}")
        
        # Firestore'dan kullanıcıyı al
        user = await firestore_manager.get_user_by_email(user_credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email veya şifre hatalı"
            )
        
        # Şifreyi doğrula
        if not verify_password(user_credentials.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email veya şifre hatalı"
            )
        
        user_data = {
            "user_id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "subscription_plan": user.get("subscription_plan", "free")
        }
        
        # Token'ları oluştur
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user_data["email"], "user_id": user_data["user_id"], "subscription_plan": user_data["subscription_plan"]},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user_data["email"], "user_id": user_data["user_id"]}
        )
        
        logger.info(f"Başarılı giriş - User: {user_data['user_id']}, IP: {client_ip}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Giriş hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Giriş sırasında bir hata oluştu"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """
    Mevcut kullanıcı bilgilerini al
    """
    try:
        # Firestore'dan kullanıcı detaylarını al
        user = await firestore_manager.get_user_by_id(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanıcı bulunamadı"
            )
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user.get("full_name", ""),
            is_active=user.get("is_active", True),
            subscription_plan=user.get("subscription_plan", "free"),
            created_at=user.get("created_at", "").isoformat() if user.get("created_at") else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kullanıcı bilgisi alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı bilgisi alınırken hata oluştu"
        )

@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    """
    Refresh token ile yeni access token al
    """
    try:
        # Refresh token'ı doğrula
        from .security import verify_token
        token_data = verify_token(refresh_token)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz refresh token"
            )
        
        # Yeni access token oluştur
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": token_data.email, "user_id": token_data.user_id, "subscription_plan": token_data.subscription_plan},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Aynı refresh token'ı döndür
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token yenileme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token yenileme sırasında hata oluştu"
        )

@router.post("/logout")
async def logout_user(current_user: TokenData = Depends(get_current_user)):
    """
    Kullanıcı çıkışı (token'ı blacklist'e ekle)
    """
    try:
        # Token blacklist'e ekleme işlemi (Redis veya database)
        # Bu kısım ileride implement edilecek
        
        logger.info(f"Kullanıcı çıkışı - User: {current_user.user_id}")
        
        return {"message": "Başarıyla çıkış yapıldı"}
        
    except Exception as e:
        logger.error(f"Çıkış hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çıkış sırasında hata oluştu"
        )