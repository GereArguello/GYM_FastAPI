from sqlmodel import Session, select
from app.auth.models import User
from app.core.security import verify_password
from app.core.enums import StatusEnum

def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()

def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(session, email)

    if not user:
        return None
    
    if user.status == StatusEnum.INACTIVE:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user