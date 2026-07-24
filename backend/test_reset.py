import sys
sys.path.insert(0, '.')

from app.database import get_db, engine
from app.services.auth_service import auth_service

print(f"Database URL: {engine.url}")

db = next(get_db())

user = auth_service.get_user_by_email(db, "admin@kaoyan.com")
print(f"User found: {user}")

if user:
    try:
        auth_service.send_password_reset_code(db, "admin@kaoyan.com")
        print("Code sent successfully")
        
        from app.models.password_reset import PasswordResetCode
        codes = db.query(PasswordResetCode).filter(PasswordResetCode.user_id == user.id).all()
        print(f"Reset codes in session: {codes}")
        
        db.commit()
        print("Committed to database")
        
        codes_after = db.query(PasswordResetCode).filter(PasswordResetCode.user_id == user.id).all()
        print(f"Reset codes after commit: {codes_after}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

db.close()