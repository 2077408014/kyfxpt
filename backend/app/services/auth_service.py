from typing import Optional, Union
from datetime import timedelta
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.auth import UserCreate, UserLogin, TokenResponse
from ..utils.jwt import verify_password, get_password_hash, create_access_token
from ..config import settings

class AuthService:
    def register(self, db: Session, user_data: UserCreate) -> User:
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        if existing_user:
            raise ValueError("用户名或邮箱已存在")
        
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    def login(self, db: Session, login_data: UserLogin) -> TokenResponse:
        user = db.query(User).filter(User.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.password):
            raise ValueError("邮箱或密码错误")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )
        return TokenResponse(access_token=access_token)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

auth_service = AuthService()