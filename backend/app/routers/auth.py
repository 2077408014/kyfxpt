from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse, AIConfigUpdate
from ..services.auth_service import auth_service
from ..utils.jwt import decode_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID"
        )
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    return user

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        user = auth_service.register(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        token = auth_service.login(db, login_data)
        return token
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    return current_user

@router.put("/ai-config", response_model=UserResponse)
async def update_ai_config(
    config: AIConfigUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if config.ai_api_key is not None:
            current_user.ai_api_key = config.ai_api_key
        if config.ai_api_base_url is not None:
            current_user.ai_api_base_url = config.ai_api_base_url
        if config.ai_api_model is not None:
            current_user.ai_api_model = config.ai_api_model
        if config.ai_api_provider is not None:
            current_user.ai_api_provider = config.ai_api_provider
        
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))